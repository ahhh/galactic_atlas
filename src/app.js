/**
 * Application wiring: the render loop, and turning navigation intents into
 * camera flights and mode changes. The only module that knows about both
 * the DOM and Three.js.
 */

import * as THREE from '../vendor/three.module.js';
import { Atlas } from './data.js';
import { SceneManager } from './scene.js';
import { CameraRig } from './camera.js';
import { GalaxyView } from './galaxy-view.js';
import { SystemView } from './system-view.js';
import { PlanetView } from './planet-view.js';
import { SearchIndex } from './search.js';
import { Navigator } from './navigation.js';
import { UI } from './ui.js';
import { CardBuilder } from './inspector.js';
import { MODES, ERAS, formatGalactic, formatKly } from './constants.js';

const GALAXY_HOME = { distance: 118, elevation: 1.2, azimuth: Math.PI / 2 };
// Aim a little west of the core so the galaxy sits centred between the side panels.
const GALAXY_CENTRE = new THREE.Vector3(-6, 0, 2);

const LIMITS = {
  [MODES.GALAXY]: { near: 0.05, far: 3000, min: 1.2, max: 260 },
  [MODES.SYSTEM]: { near: 0.01, far: 1500, min: 0.35, max: 90 },
  [MODES.PLANET]: { near: 0.01, far: 500, min: 1.3, max: 14 },
};

function supportsWebGL() {
  try {
    const canvas = document.createElement('canvas');
    return Boolean(window.WebGLRenderingContext && (canvas.getContext('webgl2') || canvas.getContext('webgl')));
  } catch {
    return false;
  }
}

class App {
  constructor() {
    this.atlas = new Atlas();
    this.clock = new THREE.Clock();
    this.showLabels = true;
    this.el = this._collectElements();
  }

  _collectElements() {
    const $ = (id) => document.getElementById(id);
    return {
      canvas: $('scene-canvas'), veil: $('transition-veil'), labelLayer: $('label-layer'),
      searchInput: $('search-input'), searchResults: $('search-results'),
      worldList: $('world-list'), listCount: $('list-count'), inspector: $('inspector'),
      breadcrumbs: $('breadcrumbs'), loading: $('loading'), loadingMessage: $('loading-message'),
      loadingBar: $('loading-bar'), toast: $('toast'),
      statusMode: $('status-mode'), statusScale: $('status-scale'), statusPosition: $('status-position'),
      statusEra: $('status-era'), statusNote: $('status-note'),
      tabButtons: Array.from(document.querySelectorAll('.tab-button')),
      tabPanels: Array.from(document.querySelectorAll('.tab-panel')),
      filterControls: {
        query: $('filter-query'), records: $('filter-records'), segmentum: $('filter-segmentum'),
        sector: $('filter-sector'), faction: $('filter-faction'), biome: $('filter-biome'),
        kind: $('filter-kind'), confidence: $('filter-confidence'), sort: $('filter-sort'),
        showOnMap: $('filter-map'),
      },
      filterReset: $('filter-reset'),
      eraButtons: Array.from(document.querySelectorAll('.era-button')),
    };
  }

  async start() {
    this.ui = new UI(this.el, {
      onSearch: (q) => this.ui.renderSearchResults(this.search.search(q)),
      onNavigate: (target) => this.go(target),
      onCardClosed: () => this._onCardClosed(),
      onFilterChange: (worlds, active) => this._onFilterChange(worlds, active),
    });

    this.ui.setLoading('Consulting the Astronomican…', 0.05);
    try {
      await this.atlas.load((message, progress) => this.ui.setLoading(message, progress));
    } catch (error) {
      this.ui.setLoading(`Could not load the atlas: ${error.message}. If you opened index.html directly from disk, serve the folder over HTTP instead (see README).`, 0);
      throw error;
    }
    if (!supportsWebGL()) {
      this.ui.setLoading('This browser cannot start WebGL, which the map needs. Try enabling hardware acceleration or another browser.', 1);
      return;
    }

    this.search = new SearchIndex(this.atlas);
    this.nav = new Navigator(this.atlas);
    this.cards = new CardBuilder(this.atlas, {
      go: (target) => this.go(target),
      closeUp: (world) => this._enterPlanetView(world),
      era: () => this.nav.era,
    });

    this.sceneManager = new SceneManager(this.el.canvas, this.el.veil, this.el.labelLayer);
    this.rig = new CameraRig(this.sceneManager.camera, this.el.canvas);
    this.galaxyView = new GalaxyView(this.sceneManager, this.atlas);
    this.galaxyView.build();
    this.systemView = new SystemView(this.sceneManager, this.atlas);
    this.planetView = new PlanetView(this.sceneManager);

    this.ui.setAtlas(this.atlas);
    this._bindControls();
    this._bindCanvas();
    window.addEventListener('resize', () => this.sceneManager.resize());

    const intent = Navigator.readUrl();
    if (intent.era && ERAS.some((e) => e.id === intent.era)) this.setEra(intent.era, { silent: true });
    this._enterMode(MODES.GALAXY, { ...GALAXY_HOME, target: GALAXY_CENTRE });
    this.ui.setLoading(null);
    this._renderLoop();

    if (intent.kind) {
      const target = { kind: intent.kind, id: intent.id, immediate: true };
      if (intent.kind === 'system' && intent.view === 'system') target.enter = true;
      if (intent.kind === 'world' && intent.view === 'galaxy') target.stay = true;
      await this.go(target);
      if (intent.kind === 'world' && intent.view === 'world') {
        const world = this.atlas.getWorld(intent.id);
        if (world) this._enterPlanetView(world);
      }
    } else {
      this.nav.set({ mode: MODES.GALAXY, selection: null, systemId: null });
      this._renderBreadcrumbs();
      this.ui.toast('Click a star or pick a world from the list. Positions are best guesses.', 5200);
    }
  }

  // --- Controls -------------------------------------------------------------

  _bindControls() {
    const toggle = (id, handler) => {
      const element = document.getElementById(id);
      element?.addEventListener('change', () => handler(element.checked));
    };
    toggle('toggle-labels', (on) => { this.showLabels = on; if (!on) this.sceneManager.clearLabels(); });
    toggle('toggle-segmenta', (on) => this.galaxyView.setLayer('segmenta', on));
    toggle('toggle-sectors', (on) => this.galaxyView.setLayer('sectors', on));
    toggle('toggle-astronomican', (on) => this.galaxyView.setLayer('astronomican', on));
    toggle('toggle-disc', (on) => this.galaxyView.setLayer('disc', on));
    toggle('toggle-orbits', (on) => this.systemView.setOrbitsVisible(on));
    toggle('toggle-generated', (on) => this.systemView.setGeneratedVisible(on));
    const speed = document.getElementById('orbit-speed');
    speed?.addEventListener('input', () => this.systemView.setSpeed(Number(speed.value) / 20));

    for (const button of this.el.eraButtons) {
      button.addEventListener('click', () => this.setEra(button.dataset.era));
    }
    document.getElementById('button-parent').addEventListener('click', () => this.go(this.nav.parent()));
    document.getElementById('button-home').addEventListener('click', () => this.go({ kind: 'galaxy' }));
    document.getElementById('button-share').addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(window.location.href);
        this.ui.toast('Link copied.');
      } catch {
        this.ui.toast(window.location.href);
      }
    });
  }

  setEra(eraId, { silent = false } = {}) {
    this.nav.era = eraId;
    this.galaxyView?.setEra(eraId);
    for (const button of this.el.eraButtons) button.classList.toggle('is-active', button.dataset.era === eraId);
    if (silent) return;
    this.nav.writeUrl();
    if (this._lastCard) this._lastCard();
    const era = ERAS.find((e) => e.id === eraId);
    this.ui.toast(era.label);
  }

  _bindCanvas() {
    let down = null;
    this.el.canvas.addEventListener('pointerdown', (e) => {
      down = { x: e.clientX, y: e.clientY };
      // Panning releases the camera from a world it is following.
      if (e.button !== 0 || e.shiftKey) this._following = null;
    });
    this.el.canvas.addEventListener('pointerup', (e) => {
      if (!down) return;
      const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y);
      down = null;
      if (moved <= 5) this._handleClick(e);
    });
    this.el.canvas.addEventListener('dblclick', (e) => {
      if (this.nav.mode !== MODES.GALAXY) return;
      const hit = this.galaxyView.pick(e.clientX, e.clientY, this.sceneManager.camera, this.el.canvas);
      if (hit) this.go({ kind: 'system', id: hit.id, enter: true });
    });
  }

  _handleClick(event) {
    const camera = this.sceneManager.camera;
    if (this.nav.mode === MODES.GALAXY) {
      const hit = this.galaxyView.pick(event.clientX, event.clientY, camera, this.el.canvas);
      if (hit) this.go({ kind: 'system', id: hit.id });
      return;
    }
    if (this.nav.mode === MODES.SYSTEM) {
      const hit = this.systemView.pick(this.sceneManager.pointerToNdc(event), camera);
      if (!hit) return;
      if (hit.kind === 'world') this.go({ kind: 'world', id: hit.id });
      else if (hit.kind === 'star') this.go({ kind: 'system', id: hit.id, enter: true });
    }
  }

  _onFilterChange(worlds, active) {
    if (!this.galaxyView) return;
    this.galaxyView.setVisibleSystems(active ? new Set(worlds.map((w) => w.system)) : null);
  }

  _onCardClosed() {
    this._lastCard = null;
    if (this.nav.mode === MODES.SYSTEM) this.systemView.select(null);
    if (this.nav.mode === MODES.GALAXY) this.galaxyView.select(null);
  }

  // --- Navigation -----------------------------------------------------------

  /** The single entry point for every navigation intent. */
  async go(target) {
    if (!target) return;
    const { kind } = target;
    if (kind === 'galaxy') return this._goGalaxy();
    if (kind === 'galaxy-at') return this._goSystem(target.id, { ...target, enter: false });
    if (kind === 'segmentum') return this._goSegmentum(target.id, target);
    if (kind === 'sector') return this._goSector(target.id, target);
    if (kind === 'feature') return this._goFeature(target.id, target);
    if (kind === 'system') return this._goSystem(target.id, target);
    if (kind === 'world') return this._goWorld(target.id, target);
    return undefined;
  }

  async _toGalaxyMode() {
    if (this.nav.mode === MODES.GALAXY) return;
    await this.sceneManager.transition(async () => {
      this._enterMode(MODES.GALAXY, { ...GALAXY_HOME, distance: 40, target: this._galaxyReturn });
    });
    this.nav.set({ mode: MODES.GALAXY, systemId: null });
  }

  _fly(options, immediate) {
    if (immediate) {
      this.rig.set(options);
      return Promise.resolve();
    }
    return new Promise((resolve) => {
      const flight = this.rig.flyTo({ duration: 1400, ...options });
      flight.onArrive = resolve;
    });
  }

  async _goGalaxy() {
    await this._toGalaxyMode();
    this.galaxyView.select(null);
    this.ui.hideCard();
    this.nav.set({ mode: MODES.GALAXY, selection: null, systemId: null });
    this._fly({ target: GALAXY_CENTRE.clone(), ...GALAXY_HOME });
    this._renderBreadcrumbs();
  }

  async _goSegmentum(name, { immediate } = {}) {
    await this._toGalaxyMode();
    const label = this.galaxyView.segmentumLabels.find((l) => l.name === name);
    if (!label) return;
    this.galaxyView.select(null);
    this.nav.set({ mode: MODES.GALAXY, selection: { kind: 'segmentum', id: name }, systemId: null });
    this._showCard(() => this.cards.segmentum(name));
    this._renderBreadcrumbs();
    this._fly({ target: label.position.clone(), distance: name === 'Solar' ? 32 : 75 }, immediate);
  }

  async _goSector(id, { immediate } = {}) {
    const sector = this.atlas.getSector(id);
    if (!sector) return;
    await this._toGalaxyMode();
    this.galaxyView.select(null);
    this.nav.set({ mode: MODES.GALAXY, selection: { kind: 'sector', id }, systemId: null });
    this._showCard(() => this.cards.sector(sector));
    this._renderBreadcrumbs();
    this._fly({ target: this.galaxyView.sectorPosition(sector), distance: Math.max(9, sector.radius * 6) }, immediate);
  }

  async _goFeature(id, { immediate } = {}) {
    await this._toGalaxyMode();
    if (id === 'great_rift' && this.nav.era !== 'post_rift') this.setEra('post_rift');
    if (id === 'eye_of_terror' && this.nav.era === 'pre_eye') this.setEra('pre_rift');
    const f = this.atlas.features;
    const position = id === 'great_rift'
      ? this.galaxyView.galacticPoint(12, 2)
      : this.galaxyView.galacticPoint(f[id].x, f[id].y);
    this.nav.set({ mode: MODES.GALAXY, selection: { kind: 'feature', id }, systemId: null });
    this._showCard(() => this.cards.feature(id));
    this._renderBreadcrumbs();
    this._fly({ target: position, distance: id === 'great_rift' ? 95 : id === 'maelstrom' ? 14 : 26 }, immediate);
  }

  /**
   * Select a system. Without `enter`, select it on the galaxy map; with
   * `enter`, travel to it and cross into the system view.
   */
  async _goSystem(id, { enter = false, focus = null, immediate = false } = {}) {
    const system = this.atlas.getSystem(id);
    if (!system) return;
    const position = this.galaxyView.systemPosition(id);
    this._galaxyReturn = position;

    if (this.nav.mode === MODES.SYSTEM && this.nav.systemId === id && enter) {
      if (focus) return this._focusWorld(focus);
      this.systemView.select(null);
      this.nav.set({ selection: { kind: 'system', id } });
      this._showCard(() => this.cards.system(system, { inSystemView: true }));
      this._renderBreadcrumbs();
      return this._fly({ target: new THREE.Vector3(), distance: this.systemView.framingDistance() });
    }

    if (!enter) {
      await this._toGalaxyMode();
      this.galaxyView.select(id);
      this.nav.set({ mode: MODES.GALAXY, selection: { kind: 'system', id }, systemId: null });
      this._showCard(() => this.cards.system(system, { inSystemView: false }));
      this._renderBreadcrumbs();
      const distance = Math.min(this.rig.currentDistance, 14);
      return this._fly({ target: position, distance }, immediate);
    }

    // Travel across the map first when starting from the galaxy view.
    if (this.nav.mode === MODES.GALAXY && !immediate) {
      this.galaxyView.select(id);
      const far = this.rig.currentDistance;
      await this._fly({ target: position, distance: Math.max(3, Math.min(far * 0.35, 12)), duration: 1300 });
    }
    const enterSystem = () => {
      this.systemView.load(system);
      this._enterMode(MODES.SYSTEM, { distance: this.systemView.framingDistance(), elevation: 0.55, azimuth: Math.PI / 2 });
    };
    if (immediate) enterSystem();
    else await this.sceneManager.transition(async () => enterSystem());

    this.nav.set({ mode: MODES.SYSTEM, selection: { kind: 'system', id }, systemId: id });
    if (focus) return this._focusWorld(focus, { immediate });
    this.systemView.select(null);
    this._showCard(() => this.cards.system(system, { inSystemView: true }));
    this._renderBreadcrumbs();
    return undefined;
  }

  async _goWorld(id, options = {}) {
    const world = this.atlas.getWorld(id);
    if (!world) return;
    this.ui.highlightWorld(id);
    if (options.stay) {
      await this._goSystem(world.system, { immediate: options.immediate });
      this.nav.set({ selection: { kind: 'world', id } });
      this._showCard(() => this.cards.world(world, { mode: this.nav.mode }));
      this._renderBreadcrumbs();
      return;
    }
    if (this.nav.mode === MODES.SYSTEM && this.nav.systemId === world.system) {
      this._focusWorld(id);
      return;
    }
    await this._goSystem(world.system, { enter: true, focus: id, immediate: options.immediate });
  }

  _focusWorld(id, { immediate = false } = {}) {
    const world = this.atlas.getWorld(id);
    if (!world.generated) this.systemView.setGeneratedVisible(this.systemView.showGenerated);
    else if (!this.systemView.showGenerated) {
      this.systemView.setGeneratedVisible(true);
      const checkbox = document.getElementById('toggle-generated');
      if (checkbox) checkbox.checked = true;
    }
    this.systemView.select(id);
    this.nav.set({ mode: MODES.SYSTEM, selection: { kind: 'world', id }, systemId: world.system });
    this._showCard(() => this.cards.world(world, { mode: MODES.SYSTEM }));
    this._renderBreadcrumbs();
    this.ui.highlightWorld(id);
    const radius = this.systemView.worldRadius(id);
    this._following = id;
    this._fly({ target: this.systemView.worldPosition(id), distance: Math.max(radius * 26, 7), duration: 1100 }, immediate);
  }

  async _enterPlanetView(world) {
    await this.sceneManager.transition(async () => {
      this.planetView.load(world);
      this._enterMode(MODES.PLANET, { distance: 3.4, elevation: 0.15, azimuth: Math.PI / 2 + 0.4 });
    });
    this._following = null;
    this.nav.set({ mode: MODES.PLANET, selection: { kind: 'world', id: world.id }, systemId: world.system });
    this._showCard(() => this.cards.world(world, { mode: MODES.PLANET }));
    this._renderBreadcrumbs();
    this.sceneManager.clearLabels();
  }

  _enterMode(mode, { target = null, distance, elevation, azimuth } = {}) {
    this.sceneManager.setMode(mode);
    const limits = LIMITS[mode];
    const camera = this.sceneManager.camera;
    camera.near = limits.near;
    camera.far = limits.far;
    camera.updateProjectionMatrix();
    this.rig.minDistance = limits.min;
    this.rig.maxDistance = limits.max;
    this.rig.set({
      target: target ? target.clone() : new THREE.Vector3(),
      distance, elevation: elevation ?? 0.6, azimuth: azimuth ?? Math.PI / 2,
    });
    this._following = null;
    this.sceneManager.clearLabels();
    if (mode === MODES.GALAXY) this.nav.mode = MODES.GALAXY;
  }

  _showCard(build) {
    this._lastCard = () => this.ui.showCard(build());
    this._lastCard();
  }

  _renderBreadcrumbs() {
    this.ui.renderBreadcrumbs(this.nav.breadcrumbs());
  }

  // --- Frame loop -----------------------------------------------------------

  _renderLoop() {
    let labelTimer = 0;
    let statusTimer = 0;
    const tick = () => {
      const delta = Math.min(this.clock.getDelta(), 0.1);
      const mode = this.sceneManager.mode;
      const camera = this.sceneManager.camera;
      if (mode === MODES.GALAXY) this.galaxyView.update(delta);
      else if (mode === MODES.SYSTEM) {
        this.systemView.update(delta, camera);
        // Keep a focused world centred while it orbits, unless the user pans.
        if (this._following && !this.rig.isFlying) {
          const p = this.systemView.worldPosition(this._following);
          this.rig.target.copy(p);
        }
      } else if (mode === MODES.PLANET) this.planetView.update(delta);
      this.rig.update();

      labelTimer += delta;
      statusTimer += delta;
      if (labelTimer > 1 / 15) {
        labelTimer = 0;
        this._updateLabels(mode, camera);
      }
      if (statusTimer > 1 / 8) {
        statusTimer = 0;
        this._updateStatus(mode, camera);
      }
      this.sceneManager.render();
      requestAnimationFrame(tick);
    };
    tick();
  }

  _updateLabels(mode, camera) {
    if (!this.showLabels || this.sceneManager.transitioning) return;
    const onSelect = (target) => this.go(target);
    let entries = [];
    if (mode === MODES.GALAXY) {
      entries = this.galaxyView.labelEntries(camera, this.rig.currentDistance, onSelect, this.el.canvas);
    } else if (mode === MODES.SYSTEM) {
      entries = this.systemView.labelEntries(onSelect);
    }
    this.sceneManager.updateLabels(entries);
  }

  _updateStatus(mode, camera) {
    const distance = this.rig.currentDistance;
    const across = 2 * distance * Math.tan((camera.fov * Math.PI) / 360) * camera.aspect;
    const era = ERAS.find((e) => e.id === this.nav.era);
    let status;
    if (mode === MODES.GALAXY) {
      const t = this.rig.target;
      const gx = t.x;
      const gy = -t.z;
      const terra = this.atlas.frame.terra;
      status = {
        mode: 'Galaxy',
        scale: `${formatKly(across)} across`,
        position: `${formatGalactic(gx, gy)} · ${formatKly(Math.hypot(gx - terra.x, gy - terra.y))} from Terra`,
        note: 'Positions are best guesses. Canon publishes no consistent galactic coordinates.',
      };
    } else if (mode === MODES.SYSTEM) {
      const system = this.atlas.getSystem(this.nav.systemId);
      status = {
        mode: 'System',
        scale: 'Schematic',
        position: system ? `${system.name} · ${system.worlds.length} ${system.worlds.length === 1 ? 'body' : 'bodies'}` : '—',
        note: 'Orbit spacing, sizes and star type are schematic. Dashed orbits are generated, undocumented worlds.',
      };
    } else {
      const world = this.atlas.getWorld(this.nav.selection?.id);
      status = {
        mode: 'World',
        scale: 'Planetary radii',
        position: world ? world.name : '—',
        note: 'Surface generated from the world type alone. Not canonical art.',
      };
    }
    this.ui.updateStatus({ ...status, era: era?.short });
  }
}

const app = new App();
app.start().catch((error) => console.error(error));
