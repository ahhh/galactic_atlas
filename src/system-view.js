/**
 * SYSTEM_VIEW: one star system, schematic.
 *
 * Orbit spacing, body sizes and star colour are all schematic. Only the
 * Sol System uses its real planetary order. Documented worlds draw with
 * solid orbits; generated, undocumented worlds draw with dashed orbits so
 * the two are never confused.
 */

import * as THREE from '../vendor/three.module.js';
import { MODES, hashString } from './constants.js';
import { biomeSwatch, specialModel } from './planet-view.js';

const BODY_SIZE = {
  gas: 0.62, hive: 0.36, forge: 0.36, temperate: 0.34, agri: 0.34, feral: 0.33, jungle: 0.34,
  ocean: 0.35, desert: 0.32, ice: 0.3, dead: 0.26, lava: 0.24, mining: 0.27, shrine: 0.33,
  fortress: 0.33, tomb: 0.3, daemon: 0.36, ork: 0.32, maiden: 0.34, alien: 0.32,
  craftworld: 0.55, webway: 0.5, station: 0.22, unknown: 0.3,
};

export function orbitRadius(slot) {
  return 2.4 + (slot - 1) * 1.55;
}

export class SystemView {
  constructor(sceneManager, atlas) {
    this.sceneManager = sceneManager;
    this.atlas = atlas;
    this.scene = sceneManager.scene(MODES.SYSTEM);
    this.root = new THREE.Group();
    this.scene.add(this.root);
    this.bodies = [];
    this.meshes = new Map();
    this.showOrbits = true;
    this.showGenerated = true;
    this.time = 0;
    this.speed = 1;

    this.scene.add(new THREE.AmbientLight(0xffffff, 0.22));
    // A faint fill so bodies without a star (craftworlds, stations) still read.
    const fill = new THREE.DirectionalLight(0xc8d4ff, 0.5);
    fill.position.set(-3, 4, 5);
    this.scene.add(fill);
    this.starLight = new THREE.PointLight(0xffffff, 2.6, 0, 0);
    this.scene.add(this.starLight);

    const ringGeometry = new THREE.RingGeometry(1.35, 1.55, 56);
    this.selectionRing = new THREE.Mesh(ringGeometry, new THREE.MeshBasicMaterial({
      color: 0xe3bf6a, side: THREE.DoubleSide, transparent: true, opacity: 0.95, depthTest: false,
    }));
    this.selectionRing.renderOrder = 50;
    this.selectionRing.visible = false;
    this.root.add(this.selectionRing);
  }

  clear() {
    for (const child of [...this.root.children]) {
      if (child === this.selectionRing) continue;
      this.root.remove(child);
      child.traverse((node) => {
        node.geometry?.dispose();
        if (node.material) {
          node.material.map?.dispose();
          node.material.dispose();
        }
      });
    }
    this.meshes.clear();
    this.bodies = [];
    this.starMesh = null;
    this.selectionRing.visible = false;
    this.selectedId = null;
  }

  load(system) {
    this.clear();
    this.system = system;
    const worlds = this.atlas.worldsOf(system.id);
    this.freeFloating = Boolean(system.free_floating);

    if (!this.freeFloating) this._buildStar(system);

    const moonCounts = new Map();
    for (const world of worlds) {
      const parentId = world.parent && worlds.some((w) => w.id === world.parent) ? world.parent : null;
      const size = BODY_SIZE[world.biome] ?? 0.3;
      let orbit;
      if (this.freeFloating) {
        orbit = { radius: 0, centre: null, phase: 0, speed: 0 };
      } else if (parentId) {
        const k = moonCounts.get(parentId) || 0;
        moonCounts.set(parentId, k + 1);
        orbit = { radius: 0.75 + k * 0.32, centre: parentId, phase: k * 2.1 + 0.6, speed: 0.9 / (1 + k * 0.4) };
      } else {
        const slot = world.slot || 1;
        const radius = orbitRadius(slot);
        orbit = { radius, centre: null, phase: (slot * 2.399963) % (Math.PI * 2), speed: 0.9 / Math.pow(radius, 1.5) };
      }
      const body = { world, size: parentId ? size * 0.5 : size, orbit };
      this.bodies.push(body);
      this._buildBody(body);
    }
    this.updatePositions();
  }

  _buildStar(system) {
    const colour = new THREE.Color(...system.star.color);
    const geometry = new THREE.SphereGeometry(1.0, 48, 32);
    this.starMesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ color: colour }));
    this.starMesh.userData = { kind: 'star', id: system.id };
    const glow = new THREE.Sprite(new THREE.SpriteMaterial({
      map: glowTexture(), color: colour, transparent: true, opacity: 0.6,
      blending: THREE.AdditiveBlending, depthWrite: false,
    }));
    glow.scale.setScalar(7);
    this.starMesh.add(glow);
    this.root.add(this.starMesh);
    this.starLight.color = colour;
  }

  _buildBody(body) {
    const { world, size, orbit } = body;
    if (!this.freeFloating && !orbit.centre) {
      const points = [];
      for (let i = 0; i <= 128; i += 1) {
        const a = (i / 128) * Math.PI * 2;
        points.push(new THREE.Vector3(Math.cos(a) * orbit.radius, 0, Math.sin(a) * orbit.radius));
      }
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = world.generated
        ? new THREE.LineDashedMaterial({ color: 0x6d7c90, transparent: true, opacity: 0.4, dashSize: 0.18, gapSize: 0.14 })
        : new THREE.LineBasicMaterial({ color: 0xc9a24f, transparent: true, opacity: 0.6 });
      const line = new THREE.Line(geometry, material);
      if (world.generated) line.computeLineDistances();
      line.userData = { kind: 'orbit', generated: Boolean(world.generated) };
      line.visible = this.showOrbits && (this.showGenerated || !world.generated);
      body.line = line;
      this.root.add(line);
    }

    const swatch = biomeSwatch(world);
    const geometry = new THREE.SphereGeometry(size, 32, 24);
    const material = new THREE.MeshStandardMaterial({
      color: new THREE.Color(swatch.mid),
      emissive: new THREE.Color(swatch.glow || '#000000'),
      emissiveIntensity: swatch.glow ? 0.6 : 0,
      roughness: 0.85,
      metalness: 0.05,
    });
    const mesh = new THREE.Mesh(geometry, material);
    const model = specialModel(world);
    if (model) {
      // Keep the sphere as an invisible pick target and show the model instead.
      material.visible = false;
      model.scale.setScalar(size * 0.75);
      mesh.add(model);
    }
    if (world.biome === 'gas') {
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(size * 1.35, size * 1.9, 48),
        new THREE.MeshBasicMaterial({ color: new THREE.Color(swatch.hot), transparent: true, opacity: 0.35, side: THREE.DoubleSide }),
      );
      ring.rotation.x = -Math.PI / 2 + 0.35;
      if (hashString(world.id) % 3 === 0) mesh.add(ring);
    }
    mesh.userData = { kind: 'world', id: world.id, radius: size };
    mesh.visible = this.showGenerated || !world.generated;
    body.mesh = mesh;
    this.meshes.set(world.id, mesh);
    this.root.add(mesh);
  }

  setOrbitsVisible(on) {
    this.showOrbits = on;
    for (const body of this.bodies) {
      if (body.line) body.line.visible = on && (this.showGenerated || !body.world.generated);
    }
  }

  setGeneratedVisible(on) {
    this.showGenerated = on;
    for (const body of this.bodies) {
      if (!body.world.generated) continue;
      body.mesh.visible = on;
      if (body.line) body.line.visible = on && this.showOrbits;
    }
  }

  setSpeed(speed) { this.speed = speed; }

  update(delta, camera) {
    this.time += delta * this.speed;
    this.updatePositions();
    if (this.selectionRing.visible) this.selectionRing.lookAt(camera.position);
  }

  updatePositions() {
    const byId = new Map(this.bodies.map((b) => [b.world.id, b]));
    for (const body of this.bodies) {
      const { orbit } = body;
      const angle = orbit.phase + this.time * orbit.speed * 0.25;
      let cx = 0;
      let cz = 0;
      if (orbit.centre) {
        const parent = byId.get(orbit.centre);
        cx = parent.mesh.position.x;
        cz = parent.mesh.position.z;
      }
      body.mesh.position.set(cx + Math.cos(angle) * orbit.radius, 0, cz + Math.sin(angle) * orbit.radius);
      if (!orbit.centre && orbit.radius === 0 && this.bodies.length > 1) {
        body.mesh.position.x = (this.bodies.indexOf(body) - (this.bodies.length - 1) / 2) * 2;
      }
      body.mesh.rotation.y += 0.002;
    }
    // Moons are positioned after their parents on the next pass.
    for (const body of this.bodies) {
      if (!body.orbit.centre) continue;
      const parent = byId.get(body.orbit.centre);
      const angle = body.orbit.phase + this.time * body.orbit.speed * 0.25;
      body.mesh.position.set(
        parent.mesh.position.x + Math.cos(angle) * body.orbit.radius, 0,
        parent.mesh.position.z + Math.sin(angle) * body.orbit.radius,
      );
    }
    this._syncRing();
  }

  select(worldId) {
    this.selectedId = worldId;
    this._syncRing();
  }

  _syncRing() {
    const mesh = this.selectedId ? this.meshes.get(this.selectedId) : null;
    if (!mesh) {
      this.selectionRing.visible = false;
      return;
    }
    this.selectionRing.visible = true;
    this.selectionRing.position.copy(mesh.position);
    this.selectionRing.scale.setScalar(mesh.userData.radius * 1.15);
  }

  worldPosition(worldId) {
    const mesh = this.meshes.get(worldId);
    return mesh ? mesh.position.clone() : new THREE.Vector3();
  }

  worldRadius(worldId) {
    return this.meshes.get(worldId)?.userData.radius || 0.3;
  }

  pick(ndc, camera) {
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(ndc, camera);
    const targets = [...this.meshes.values()].filter((m) => m.visible);
    if (this.starMesh) targets.push(this.starMesh);
    const hits = raycaster.intersectObjects(targets, false);
    if (hits.length) return hits[0].object.userData;
    // Small bodies are hard to hit: fall back to the nearest on screen.
    let best = null;
    let bestDistance = 0.05;
    const projected = new THREE.Vector3();
    for (const mesh of targets) {
      projected.copy(mesh.position).project(camera);
      const d = Math.hypot(projected.x - ndc.x, projected.y - ndc.y);
      if (d < bestDistance) { bestDistance = d; best = mesh.userData; }
    }
    return best;
  }

  labelEntries(onSelect) {
    const entries = [];
    if (this.starMesh) {
      entries.push({
        id: `star-${this.system.id}`, text: this.system.star.label,
        position: this.starMesh.position.clone().add(new THREE.Vector3(0, 0, 1.5)),
        className: 'is-star', centred: true,
        onSelect: () => onSelect({ kind: 'system', id: this.system.id }),
      });
    }
    for (const body of this.bodies) {
      if (!body.mesh.visible) continue;
      const { world } = body;
      entries.push({
        id: `world-${world.id}`,
        text: world.name,
        position: body.mesh.position.clone(),
        className: [
          world.id === this.selectedId ? 'is-selected' : '',
          world.generated ? 'is-generated' : 'is-documented',
          body.orbit.centre ? 'is-moon' : '',
        ].join(' '),
        onSelect: () => onSelect({ kind: 'world', id: world.id }),
      });
    }
    return entries;
  }

  framingDistance() {
    if (this.freeFloating) return 5;
    let outer = 3;
    for (const body of this.bodies) {
      if (!body.orbit.centre) outer = Math.max(outer, body.orbit.radius);
    }
    return outer * 2.2;
  }
}

let cachedGlow = null;
function glowTexture() {
  if (cachedGlow) return cachedGlow;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  gradient.addColorStop(0, 'rgba(255,255,255,1)');
  gradient.addColorStop(0.2, 'rgba(255,255,255,0.5)');
  gradient.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 128, 128);
  cachedGlow = new THREE.CanvasTexture(canvas);
  return cachedGlow;
}
