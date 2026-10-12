/**
 * Navigation state: the active mode, the selection, the breadcrumb trail
 * and the shareable URL. Knows nothing about Three.js.
 */

import { MODES } from './constants.js';

export class Navigator {
  constructor(atlas) {
    this.atlas = atlas;
    this.mode = MODES.GALAXY;
    this.selection = null; // { kind: 'world' | 'system' | 'sector' | 'segmentum' | 'feature' | 'event' | 'book', id }
    this.systemId = null;
    this.era = 'pre_rift';
  }

  set({ mode, selection, systemId }) {
    if (mode) this.mode = mode;
    if (selection !== undefined) this.selection = selection;
    if (systemId !== undefined) this.systemId = systemId;
    this.writeUrl();
  }

  /** Galaxy / Segmentum / Sector / System / World */
  breadcrumbs() {
    const trail = [{ label: 'Galaxy', action: { kind: 'galaxy' } }];
    const { atlas } = this;
    const sel = this.selection;
    let world = null;
    let system = null;
    let sector = null;
    let segmentum = null;

    if (sel?.kind === 'book') {
      const book = atlas.getBook(sel.id);
      return [...trail, { label: 'Black Library', action: null }, { label: book?.title || sel.id, action: null }];
    }
    const event = sel?.kind === 'event' ? atlas.getEvent(sel.id) : null;
    if (event?.at?.kind === 'world') world = atlas.getWorld(event.at.id);
    else if (event?.at?.kind === 'sector') sector = atlas.getSector(event.at.id);
    if (sel?.kind === 'world') world = atlas.getWorld(sel.id);
    if (world) system = atlas.getSystem(world.system);
    else if (sel?.kind === 'system') system = atlas.getSystem(sel.id);
    else if (this.systemId) system = atlas.getSystem(this.systemId);

    const anchor = world || (system && atlas.getWorld(system.primary));
    if (sel?.kind === 'sector') sector = atlas.getSector(sel.id);
    else if (sector) { /* placed by an event */ }
    else if (anchor?.sector_id) sector = atlas.getSector(anchor.sector_id);
    else if (system?.sector_id) sector = atlas.getSector(system.sector_id);

    if (sel?.kind === 'segmentum') segmentum = sel.id;
    else if (sector) segmentum = sector.segmentum || sector.segmentum_estimated;
    else if (anchor) segmentum = atlas.segmentumOf(anchor);

    if (segmentum) trail.push({ label: `Segmentum ${segmentum}`, action: { kind: 'segmentum', id: segmentum } });
    if (sector) trail.push({ label: sector.name, action: { kind: 'sector', id: sector.id } });
    if (system && !system.free_floating) {
      trail.push({
        label: system.synthetic ? `${system.name} system` : `${system.name} System`,
        action: { kind: 'system', id: system.id, enter: true },
      });
    }
    if (world) trail.push({ label: world.name, action: { kind: 'world', id: world.id } });
    if (sel?.kind === 'feature' || event?.at?.kind === 'feature') {
      const id = sel.kind === 'feature' ? sel.id : event.at.id;
      trail.push({ label: featureName(id), action: { kind: 'feature', id } });
    }
    if (event) trail.push({ label: event.name, action: null });
    return trail;
  }

  parent() {
    const sel = this.selection;
    if (this.mode === MODES.PLANET && sel?.kind === 'world') return { kind: 'world', id: sel.id };
    if (this.mode === MODES.SYSTEM) {
      if (sel?.kind === 'world') return { kind: 'system', id: this.systemId, enter: true };
      return { kind: 'system', id: this.systemId };
    }
    if (sel?.kind === 'event') {
      const event = this.atlas.getEvent(sel.id);
      if (event?.at) return { kind: event.at.kind, id: event.at.id };
    }
    if (sel?.kind === 'system' || sel?.kind === 'world') {
      const system = this.atlas.getSystem(sel.kind === 'world' ? this.atlas.getWorld(sel.id)?.system : sel.id);
      const sectorId = system?.sector_id || this.atlas.getWorld(system?.primary)?.sector_id;
      if (sectorId) return { kind: 'sector', id: sectorId };
    }
    return { kind: 'galaxy' };
  }

  writeUrl() {
    const params = new URLSearchParams();
    const sel = this.selection;
    if (sel) params.set(sel.kind, sel.id);
    if (this.mode === MODES.SYSTEM) params.set('view', 'system');
    if (this.mode === MODES.PLANET) params.set('view', 'world');
    if (this.era !== 'pre_rift') params.set('era', this.era);
    const query = params.toString();
    window.history.replaceState({}, '', `${window.location.pathname}${query ? `?${query}` : ''}`);
  }

  static readUrl() {
    const params = new URLSearchParams(window.location.search);
    const intent = { era: params.get('era'), view: params.get('view') };
    for (const kind of ['world', 'system', 'sector', 'segmentum', 'feature', 'event', 'book']) {
      if (params.get(kind)) return { ...intent, kind, id: params.get(kind) };
    }
    return intent;
  }
}

export function featureName(id) {
  return { eye_of_terror: 'Eye of Terror', maelstrom: 'Maelstrom', great_rift: 'Cicatrix Maledictum' }[id] || id;
}
