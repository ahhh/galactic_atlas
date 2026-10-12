/**
 * GALAXY_VIEW: the whole galaxy, in thousands of light years.
 *
 * Draws a decorative spiral disc, the segmentum boundaries, sector
 * footprints, the warp storms and one marker per star system. The disc's
 * arms are decoration only. Every system marker sits at the best-guess
 * position from the build script.
 *
 * The lore layer draws a diamond sigil wherever a notable event happened,
 * coloured by the kind of event. Events of the era being shown are bright;
 * the rest are dimmed, so switching eras moves the map through time.
 */

import * as THREE from '../vendor/three.module.js';
import { MODES, FACTIONS, toScene } from './constants.js';
import { eventKind } from './lore.js';

const NOISE_GLSL = `
  float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 i = floor(p); vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
               mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
  }
  float fbm(vec2 p) {
    float t = 0.0; float a = 0.5;
    for (int i = 0; i < 5; i++) { t += noise(p) * a; p *= 2.07; a *= 0.5; }
    return t;
  }
`;

function vec(x, y, z = 0) {
  const p = toScene(x, y, z);
  return new THREE.Vector3(p.x, p.y, p.z);
}

function seeded(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function gaussian(random) {
  const u = Math.max(1e-9, random());
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * random());
}

function radialTexture(stops) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  for (const [offset, colour] of stops) gradient.addColorStop(offset, colour);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 128, 128);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function ringTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  ctx.strokeStyle = 'rgba(255, 214, 128, 1)';
  ctx.lineWidth = 6;
  ctx.beginPath();
  ctx.arc(64, 64, 52, 0, Math.PI * 2);
  ctx.stroke();
  ctx.lineWidth = 3;
  for (let i = 0; i < 4; i += 1) {
    const a = (i * Math.PI) / 2;
    ctx.beginPath();
    ctx.moveTo(64 + Math.cos(a) * 40, 64 + Math.sin(a) * 40);
    ctx.lineTo(64 + Math.cos(a) * 62, 64 + Math.sin(a) * 62);
    ctx.stroke();
  }
  return new THREE.CanvasTexture(canvas);
}

export class GalaxyView {
  constructor(sceneManager, atlas) {
    this.sceneManager = sceneManager;
    this.atlas = atlas;
    this.scene = sceneManager.scene(MODES.GALAXY);
    this.root = new THREE.Group();
    this.scene.add(this.root);
    this.time = 0;
    this.selectedSystem = null;
    this.visibleSystems = null;
    this.highlightSystems = null;
    this.layers = { segmenta: true, sectors: false, astronomican: false, disc: true, lore: true };
    this.era = 'pre_rift';
  }

  build() {
    const { frame, features } = this.atlas;
    this.R = frame.galaxy_radius;
    this.terra = frame.terra;
    this._buildDisc();
    this._buildCore();
    this._buildSegmenta(frame);
    this._buildSectors();
    this._buildAstronomican(frame);
    this.eye = this._buildStorm(features.eye_of_terror, [0.55, 0.12, 0.62], [0.95, 0.3, 0.45], 1.7);
    this.maelstrom = this._buildStorm(features.maelstrom, [0.25, 0.18, 0.7], [0.75, 0.35, 0.9], 1.9);
    this._buildRift(features.great_rift);
    this._buildSystems();
    this._buildLore();
    this._buildSelection();
    this.setEra(this.era);
  }

  // --- Decoration --------------------------------------------------------

  _buildDisc() {
    const random = seeded(40000);
    const count = 90000;
    const positions = new Float32Array(count * 3);
    const colours = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const arms = 4;
    const colour = new THREE.Color();
    for (let i = 0; i < count; i += 1) {
      let x;
      let y;
      let r;
      const bulge = random() < 0.1;
      if (bulge) {
        r = Math.abs(gaussian(random)) * 4.5;
        const a = random() * Math.PI * 2;
        x = Math.cos(a) * r * 1.25;
        y = Math.sin(a) * r;
      } else {
        r = 3 + Math.pow(random(), 0.85) * (this.R + 2);
        const arm = Math.floor(random() * arms);
        const spread = gaussian(random) * (0.12 + r * 0.0035);
        const a = arm * ((Math.PI * 2) / arms) + Math.log(r) * 2.2 + spread;
        const jitter = random() < 0.3 ? 3.2 : 0.7;
        x = Math.cos(a) * r + gaussian(random) * jitter;
        y = Math.sin(a) * r + gaussian(random) * jitter;
      }
      const thickness = Math.max(0.15, 1.1 * (1 - r / (this.R + 6)));
      const p = toScene(x, y, gaussian(random) * thickness * (bulge ? 1.6 : 0.5));
      positions[i * 3] = p.x;
      positions[i * 3 + 1] = p.y;
      positions[i * 3 + 2] = p.z;
      const t = Math.min(1, r / this.R);
      if (bulge) colour.setRGB(1.0, 0.82 - random() * 0.1, 0.55);
      else if (random() < 0.05) colour.setRGB(0.95, 0.45, 0.55);
      else colour.setRGB(0.75 + 0.2 * (1 - t), 0.78 + 0.1 * (1 - t), 0.85 + 0.15 * t);
      colours[i * 3] = colour.r;
      colours[i * 3 + 1] = colour.g;
      colours[i * 3 + 2] = colour.b;
      sizes[i] = (bulge ? 1.8 : 1.2) + random() * 1.6;
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colours, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    const material = new THREE.ShaderMaterial({
      uniforms: { uPixelRatio: { value: this.sceneManager.renderer.getPixelRatio() }, uOpacity: { value: 0.42 } },
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        varying vec3 vColor;
        uniform float uPixelRatio;
        void main() {
          vColor = color;
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          gl_Position = projectionMatrix * mv;
          gl_PointSize = size * uPixelRatio * clamp(60.0 / -mv.z, 0.6, 4.0);
        }`,
      fragmentShader: `
        varying vec3 vColor;
        uniform float uOpacity;
        void main() {
          float d = length(gl_PointCoord - 0.5);
          float a = smoothstep(0.5, 0.0, d);
          gl_FragColor = vec4(vColor, a * uOpacity);
        }`,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    this.disc = new THREE.Points(geometry, material);
    this.disc.renderOrder = -10;
    this.root.add(this.disc);
  }

  _buildCore() {
    const material = new THREE.SpriteMaterial({
      map: radialTexture([[0, 'rgba(255,236,190,0.5)'], [0.3, 'rgba(255,200,130,0.16)'], [1, 'rgba(255,160,90,0)']]),
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    });
    this.core = new THREE.Sprite(material);
    this.core.scale.setScalar(14);
    this.root.add(this.core);
  }

  _line(points, colour, opacity, dashed = false) {
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = dashed
      ? new THREE.LineDashedMaterial({ color: colour, transparent: true, opacity, dashSize: 0.8, gapSize: 0.6, depthWrite: false })
      : new THREE.LineBasicMaterial({ color: colour, transparent: true, opacity, depthWrite: false });
    const line = new THREE.Line(geometry, material);
    if (dashed) line.computeLineDistances();
    return line;
  }

  _circle(cx, cy, radius, segments = 96) {
    const points = [];
    for (let i = 0; i <= segments; i += 1) {
      const a = (i / segments) * Math.PI * 2;
      points.push(vec(cx + Math.cos(a) * radius, cy + Math.sin(a) * radius));
    }
    return points;
  }

  _buildSegmenta(frame) {
    this.segmentaGroup = new THREE.Group();
    const gold = 0xd9b25f;
    const { terra, solar_radius: solarRadius, wedges } = frame;
    this.segmentaGroup.add(this._line(this._circle(terra.x, terra.y, solarRadius), gold, 0.55));
    // Rays from the Solar boundary to the rim at each wedge boundary.
    const rim = this.R + 2;
    const boundaries = new Set();
    for (const [start, end] of Object.values(wedges)) { boundaries.add(start); boundaries.add(end); }
    for (const angle of boundaries) {
      const a = (angle * Math.PI) / 180;
      const dx = Math.cos(a);
      const dy = Math.sin(a);
      // Solve |terra + t d| = rim for t > 0.
      const b = terra.x * dx + terra.y * dy;
      const c = terra.x ** 2 + terra.y ** 2 - rim ** 2;
      const t = -b + Math.sqrt(b * b - c);
      this.segmentaGroup.add(this._line([
        vec(terra.x + dx * solarRadius, terra.y + dy * solarRadius),
        vec(terra.x + dx * t, terra.y + dy * t),
      ], gold, 0.4, true));
    }
    this.segmentaGroup.add(this._line(this._circle(0, 0, rim, 160), gold, 0.18, true));

    // Label anchors halfway out along each wedge's bisector.
    this.segmentumLabels = [{ name: 'Solar', position: vec(terra.x, terra.y - solarRadius * 0.55) }];
    for (const [name, [start, end]] of Object.entries(wedges)) {
      const a = (((start + end) / 2) * Math.PI) / 180;
      const dx = Math.cos(a);
      const dy = Math.sin(a);
      const b = terra.x * dx + terra.y * dy;
      const c = terra.x ** 2 + terra.y ** 2 - rim ** 2;
      const t = -b + Math.sqrt(b * b - c);
      const d = solarRadius + (t - solarRadius) * (name === 'Pacificus' ? 0.62 : 0.55);
      this.segmentumLabels.push({ name, position: vec(terra.x + dx * d, terra.y + dy * d) });
    }
    this.root.add(this.segmentaGroup);
  }

  _buildSectors() {
    this.sectorGroup = new THREE.Group();
    this.sectorLabels = [];
    for (const sector of this.atlas.sectors.values()) {
      const anchored = sector.placement.method === 'anchor';
      const line = this._line(this._circle(sector.x, sector.y, sector.radius, 48),
        anchored ? 0x9fb7d0 : 0x6c7f94, anchored ? 0.4 : 0.22, !anchored);
      this.sectorGroup.add(line);
      this.sectorLabels.push({ sector, position: vec(sector.x, sector.y + sector.radius + 0.3) });
    }
    this.sectorGroup.visible = this.layers.sectors;
    this.root.add(this.sectorGroup);
  }

  _buildAstronomican(frame) {
    this.astronomican = this._line(this._circle(frame.terra.x, frame.terra.y, 50, 180), 0xffe3a0, 0.35, true);
    this.astronomican.visible = this.layers.astronomican;
    this.root.add(this.astronomican);
  }

  _buildStorm(feature, inner, outer, scale) {
    const geometry = new THREE.PlaneGeometry(1, 1);
    const material = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uInner: { value: new THREE.Color(...inner) },
        uOuter: { value: new THREE.Color(...outer) },
      },
      vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader: `
        varying vec2 vUv;
        uniform float uTime;
        uniform vec3 uInner;
        uniform vec3 uOuter;
        ${NOISE_GLSL}
        void main() {
          vec2 p = vUv * 2.0 - 1.0;
          float r = length(p);
          float a = atan(p.y, p.x);
          float swirl = a + r * 5.0 - uTime * 0.15;
          float n = fbm(vec2(cos(swirl), sin(swirl)) * (1.5 + r * 2.5) + vec2(uTime * 0.03, r * 3.0));
          float body = smoothstep(1.0, 0.35, r);
          float alpha = body * (0.25 + 0.95 * n);
          vec3 colour = mix(uInner, uOuter, smoothstep(0.3, 0.8, n));
          float pupil = smoothstep(0.32, 0.12, r);
          colour = mix(colour, vec3(0.08, 0.0, 0.05), pupil * 0.75);
          alpha = max(alpha, pupil * 0.85);
          gl_FragColor = vec4(colour, alpha * 0.85);
        }`,
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.x = -Math.PI / 2;
    const p = vec(feature.x, feature.y, 0.02);
    mesh.position.copy(p);
    mesh.scale.setScalar(feature.r * 2 * scale);
    mesh.renderOrder = 2;
    this.root.add(mesh);
    return mesh;
  }

  _buildRift(points) {
    const curve = new THREE.CatmullRomCurve3(points.map((p) => vec(p.x, p.y, 0.03)));
    const samples = 240;
    const positions = [];
    const uvs = [];
    const indices = [];
    for (let i = 0; i <= samples; i += 1) {
      const t = i / samples;
      const point = curve.getPointAt(t);
      const tangent = curve.getTangentAt(t);
      const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
      const width = 0.8 + 3.0 * Math.sin(Math.PI * Math.min(1, t * 1.15)) ** 0.7;
      for (const side of [-1, 1]) {
        const p = point.clone().addScaledVector(normal, side * width);
        positions.push(p.x, p.y, p.z);
        uvs.push(t, side < 0 ? 0 : 1);
      }
      if (i < samples) {
        const a = i * 2;
        indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    geometry.setIndex(indices);
    const material = new THREE.ShaderMaterial({
      uniforms: { uTime: { value: 0 } },
      vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader: `
        varying vec2 vUv;
        uniform float uTime;
        ${NOISE_GLSL}
        void main() {
          float across = abs(vUv.y * 2.0 - 1.0);
          float n = fbm(vec2(vUv.x * 28.0 + uTime * 0.05, vUv.y * 3.0 - uTime * 0.1));
          float edge = 1.0 - smoothstep(0.25 + n * 0.5, 1.0, across);
          float alpha = edge * (0.25 + n * 0.85);
          vec3 colour = mix(vec3(0.45, 0.08, 0.55), vec3(0.95, 0.3, 0.6), n);
          colour = mix(colour, vec3(1.0, 0.75, 0.9), smoothstep(0.75, 1.0, n) * (1.0 - across));
          gl_FragColor = vec4(colour, alpha * 0.8);
        }`,
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    this.rift = new THREE.Mesh(geometry, material);
    this.rift.renderOrder = 3;
    this.riftLabelPosition = curve.getPointAt(0.55).add(new THREE.Vector3(0, 0, -3.2));
    this.root.add(this.rift);
  }

  // --- Systems ------------------------------------------------------------

  _buildSystems() {
    const systems = Array.from(this.atlas.systems.values());
    this.systemList = systems;
    this.systemIndex = new Map(systems.map((s, i) => [s.id, i]));
    const count = systems.length;
    const positions = new Float32Array(count * 3);
    const colours = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const alphas = new Float32Array(count);
    const colour = new THREE.Color();
    this.positions = [];
    systems.forEach((system, i) => {
      const primary = this.atlas.getWorld(system.primary);
      const p = vec(system.x, system.y, primary?.z || 0);
      this.positions.push(p);
      positions.set([p.x, p.y, p.z], i * 3);
      colour.set((FACTIONS[system.faction] || FACTIONS.unknown).color);
      colours.set([colour.r, colour.g, colour.b], i * 3);
      const prominence = primary?.generated ? 0 : primary?.prominence || 1;
      sizes[i] = [4.2, 5.4, 6.6, 9.5][prominence];
      alphas[i] = 1;
    });
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colours, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    geometry.setAttribute('alpha', new THREE.BufferAttribute(alphas, 1));
    const material = new THREE.ShaderMaterial({
      uniforms: { uPixelRatio: { value: this.sceneManager.renderer.getPixelRatio() } },
      vertexShader: `
        attribute float size;
        attribute float alpha;
        attribute vec3 color;
        varying vec3 vColor;
        varying float vAlpha;
        uniform float uPixelRatio;
        void main() {
          vColor = color;
          vAlpha = alpha;
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          gl_Position = projectionMatrix * mv;
          gl_PointSize = size * uPixelRatio * clamp(70.0 / -mv.z, 0.75, 2.6) * (alpha < 0.5 ? 0.6 : 1.0);
        }`,
      fragmentShader: `
        varying vec3 vColor;
        varying float vAlpha;
        void main() {
          float d = length(gl_PointCoord - 0.5);
          if (d > 0.5) discard;
          float core = smoothstep(0.22, 0.0, d);
          float halo = smoothstep(0.5, 0.15, d);
          vec3 c = mix(vColor, vec3(1.0), core * 0.6);
          gl_FragColor = vec4(c, (halo * 0.85 + core * 0.3) * vAlpha);
        }`,
      transparent: true,
      depthWrite: false,
    });
    this.systemPoints = new THREE.Points(geometry, material);
    this.systemPoints.renderOrder = 10;
    this.root.add(this.systemPoints);
  }

  /** One sigil per place where events happened; co-located events share it. */
  _buildLore() {
    const sites = new Map();
    for (const event of this.atlas.chronicle) {
      if (event.x === undefined) continue;
      const key = `${event.x.toFixed(2)},${event.y.toFixed(2)}`;
      if (!sites.has(key)) {
        const at = event.at?.kind === 'world' ? this.atlas.getWorld(event.at.id) : null;
        sites.set(key, { position: vec(event.x, event.y, at?.z || 0), events: [] });
      }
      sites.get(key).events.push(event);
    }
    this.loreSites = Array.from(sites.values());
    const count = this.loreSites.length;
    const positions = new Float32Array(count * 3);
    const colours = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const alphas = new Float32Array(count);
    const colour = new THREE.Color();
    this.loreSites.forEach((site, i) => {
      site.events.sort((a, b) => (b.weight || 1) - (a.weight || 1) || b.sort - a.sort);
      site.top = site.events[0];
      site.weight = Math.max(...site.events.map((e) => e.weight || 1));
      positions.set([site.position.x, site.position.y, site.position.z], i * 3);
      colour.set(eventKind(site.top).color);
      colours.set([colour.r, colour.g, colour.b], i * 3);
      sizes[i] = 13 + site.weight * 4 + Math.min(site.events.length - 1, 3) * 1.5;
      alphas[i] = 1;
    });
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colours, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    geometry.setAttribute('alpha', new THREE.BufferAttribute(alphas, 1));
    const material = new THREE.ShaderMaterial({
      uniforms: { uPixelRatio: { value: this.sceneManager.renderer.getPixelRatio() }, uTime: { value: 0 } },
      vertexShader: `
        attribute float size;
        attribute float alpha;
        attribute vec3 color;
        varying vec3 vColor;
        varying float vAlpha;
        uniform float uPixelRatio;
        void main() {
          vColor = color;
          vAlpha = alpha;
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          gl_Position = projectionMatrix * mv;
          gl_PointSize = size * uPixelRatio * clamp(60.0 / -mv.z, 0.7, 1.8);
        }`,
      fragmentShader: `
        varying vec3 vColor;
        varying float vAlpha;
        uniform float uTime;
        void main() {
          vec2 p = gl_PointCoord - 0.5;
          float d = abs(p.x) + abs(p.y);
          if (d > 0.5) discard;
          float ring = smoothstep(0.05, 0.0, abs(d - 0.38));
          float glow = smoothstep(0.5, 0.3, d) * 0.22 * (0.75 + 0.25 * sin(uTime * 1.6));
          gl_FragColor = vec4(mix(vColor, vec3(1.0), ring * 0.25), (ring * 0.95 + glow) * vAlpha);
        }`,
      transparent: true,
      depthWrite: false,
    });
    this.lorePoints = new THREE.Points(geometry, material);
    this.lorePoints.renderOrder = 9;
    this.root.add(this.lorePoints);
  }

  _refreshLore() {
    if (!this.lorePoints) return;
    const alpha = this.lorePoints.geometry.getAttribute('alpha');
    this.loreSites.forEach((site, i) => {
      site.inEra = site.events.some((e) => e.era === this.era);
      site.highlighted = Boolean(this.highlightSystems) && site.events.some((e) => (e.worlds || [])
        .some((w) => this.highlightSystems.has(this.atlas.getWorld(w)?.system)));
      const dim = this.highlightSystems && !site.highlighted ? 0.18 : 1;
      alpha.array[i] = (site.inEra ? 1 : 0.28) * dim;
    });
    alpha.needsUpdate = true;
  }

  _buildSelection() {
    const material = new THREE.SpriteMaterial({
      map: ringTexture(), transparent: true, depthTest: false, depthWrite: false, sizeAttenuation: false,
    });
    this.selectionSprite = new THREE.Sprite(material);
    this.selectionSprite.scale.setScalar(0.045);
    this.selectionSprite.visible = false;
    this.selectionSprite.renderOrder = 20;
    this.root.add(this.selectionSprite);
  }

  // --- Public API ---------------------------------------------------------

  setEra(eraId) {
    this.era = eraId;
    const hasEye = eraId !== 'pre_eye';
    this.eye.visible = hasEye;
    this.rift.visible = eraId === 'post_rift';
    this._refreshLore();
  }

  setLayer(name, on) {
    this.layers[name] = on;
    if (name === 'segmenta') this.segmentaGroup.visible = on;
    if (name === 'sectors') this.sectorGroup.visible = on;
    if (name === 'astronomican') this.astronomican.visible = on;
    if (name === 'disc') { this.disc.visible = on; this.core.visible = on; }
    if (name === 'lore') this.lorePoints.visible = on;
  }

  /** Dim every system not in `ids` (a Set), or show all when null. */
  setVisibleSystems(ids) {
    this.visibleSystems = ids;
    this._refreshAlpha();
  }

  /** Light up the systems a book or event is linked to (a Set), or clear with null. */
  setHighlight(ids) {
    this.highlightSystems = ids && ids.size ? ids : null;
    this._refreshAlpha();
  }

  _refreshAlpha() {
    const ids = this.highlightSystems || this.visibleSystems;
    const alpha = this.systemPoints.geometry.getAttribute('alpha');
    this.systemList.forEach((system, i) => {
      alpha.array[i] = !ids || ids.has(system.id) ? 1 : 0.14;
    });
    alpha.needsUpdate = true;
    this._refreshLore();
  }

  select(systemId) {
    this.selectedSystem = systemId;
    const index = this.systemIndex.get(systemId);
    if (index === undefined) {
      this.selectionSprite.visible = false;
      return;
    }
    this.selectionSprite.position.copy(this.positions[index]);
    this.selectionSprite.visible = true;
  }

  systemPosition(systemId) {
    const index = this.systemIndex.get(systemId);
    return index === undefined ? new THREE.Vector3() : this.positions[index].clone();
  }

  sectorPosition(sector) { return vec(sector.x, sector.y); }

  galacticPoint(x, y) { return vec(x, y); }

  update(delta) {
    this.time += delta;
    this.eye.material.uniforms.uTime.value = this.time;
    this.maelstrom.material.uniforms.uTime.value = this.time * 1.3;
    this.rift.material.uniforms.uTime.value = this.time;
    this.lorePoints.material.uniforms.uTime.value = this.time;
  }

  /** Nearest system marker to a screen point, within a few pixels. */
  pick(clientX, clientY, camera, canvas) {
    const rect = canvas.getBoundingClientRect();
    const projected = new THREE.Vector3();
    let best = null;
    let bestDistance = 14;
    this.systemList.forEach((system, i) => {
      if (this.visibleSystems && !this.visibleSystems.has(system.id)) return;
      projected.copy(this.positions[i]).project(camera);
      if (projected.z > 1) return;
      const sx = rect.left + (projected.x * 0.5 + 0.5) * rect.width;
      const sy = rect.top + (-projected.y * 0.5 + 0.5) * rect.height;
      const d = Math.hypot(sx - clientX, sy - clientY);
      const primary = this.atlas.getWorld(system.primary);
      const bias = primary && !primary.generated ? primary.prominence * 1.5 : 0;
      if (d - bias < bestDistance) {
        bestDistance = d - bias;
        best = system;
      }
    });
    return best;
  }

  /**
   * Label candidates, ranked and decluttered in screen space so the overlay
   * stays readable at every zoom level.
   */
  labelEntries(camera, distance, onSelect, canvas) {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const candidates = [];
    const add = (entry, priority) => candidates.push({ ...entry, priority });

    if (this.layers.segmenta && distance > 35) {
      for (const label of this.segmentumLabels) {
        add({
          id: `seg-${label.name}`, text: `Segmentum ${label.name}`, position: label.position,
          className: 'is-segmentum', onSelect: () => onSelect({ kind: 'segmentum', id: label.name }),
        }, 100);
      }
    }
    if (distance > 18 && distance < 150) {
      for (const region of this.atlas.features.regions) {
        if (region.era && region.era !== this.era) continue;
        add({
          id: `region-${region.name}`, text: region.name, position: vec(region.x, region.y),
          className: region.kind === 'era' ? 'is-era' : 'is-region',
        }, 60);
      }
      if (this.eye.visible) {
        const f = this.atlas.features.eye_of_terror;
        add({ id: 'feature-eye', text: 'Eye of Terror', position: vec(f.x, f.y - f.r * 1.5), className: 'is-warp',
          onSelect: () => onSelect({ kind: 'feature', id: 'eye_of_terror' }) }, 95);
      }
      const m = this.atlas.features.maelstrom;
      add({ id: 'feature-maelstrom', text: 'Maelstrom', position: vec(m.x, m.y - m.r * 1.8), className: 'is-warp',
        onSelect: () => onSelect({ kind: 'feature', id: 'maelstrom' }) }, 70);
      if (this.rift.visible) {
        add({ id: 'feature-rift', text: 'Cicatrix Maledictum', position: this.riftLabelPosition, className: 'is-warp',
          onSelect: () => onSelect({ kind: 'feature', id: 'great_rift' }) }, 94);
      }
    }
    if (distance < 70) {
      for (const { sector, position } of this.sectorLabels) {
        const anchored = sector.placement.method === 'anchor';
        if (!anchored && distance > 30 && !this.layers.sectors) continue;
        add({
          id: `sector-${sector.id}`, text: sector.name, position, className: 'is-sector',
          onSelect: () => onSelect({ kind: 'sector', id: sector.id }),
        }, anchored ? 55 : 30);
      }
    }
    if (this.layers.lore) {
      // Weight-3 events are labelled from far out; minor ones only up close.
      const loreThreshold = [0, 16, 34, 80];
      for (const site of this.loreSites) {
        const highlighted = site.highlighted;
        if (this.highlightSystems && !highlighted) continue;
        const reach = site.inEra ? loreThreshold[site.weight] : 12;
        if (!highlighted && distance > reach) continue;
        const extra = site.events.length > 1 ? `  +${site.events.length - 1}` : '';
        add({
          id: `lore-${site.top.id}`, text: `${site.top.name}${extra}`, position: site.position,
          className: `is-event kind-${site.top.kind}${site.inEra ? '' : ' is-other-era'}`, offsetY: 21,
          onSelect: () => onSelect({ kind: 'event', id: site.top.id }),
        }, (highlighted ? 300 : 45) + site.weight * 14 + (site.inEra ? 10 : 0));
      }
    }
    const systemThreshold = [6, 14, 34, 110];
    this.systemList.forEach((system, i) => {
      if (this.visibleSystems && !this.visibleSystems.has(system.id)) return;
      const primary = this.atlas.getWorld(system.primary);
      const prominence = primary && !primary.generated ? primary.prominence : 0;
      const selected = system.id === this.selectedSystem;
      if (!selected && distance > systemThreshold[prominence]) return;
      add({
        id: `sys-${system.id}`,
        text: system.id === 'solar-sol' ? 'Terra' : (primary && !primary.generated ? primary.name : system.name),
        position: this.positions[i],
        className: selected ? 'is-selected' : prominence >= 3 ? 'is-major' : prominence === 0 ? 'is-minor' : '',
        onSelect: () => onSelect({ kind: 'system', id: system.id }),
      }, selected ? 1000 : 40 + prominence * 12);
    });

    // Project and declutter.
    const projected = new THREE.Vector3();
    const accepted = [];
    const boxes = [];
    candidates.sort((a, b) => b.priority - a.priority);
    for (const entry of candidates) {
      projected.copy(entry.position).project(camera);
      if (projected.z > 1 || Math.abs(projected.x) > 1.05 || Math.abs(projected.y) > 1.05) continue;
      const sx = (projected.x * 0.5 + 0.5) * width;
      const sy = (-projected.y * 0.5 + 0.5) * height + (entry.offsetY || 0);
      const perChar = /is-segmentum/.test(entry.className) ? 14.5 : /is-(era|warp)/.test(entry.className) ? 11
        : /is-(region|sector)/.test(entry.className) ? 9.5 : /is-event/.test(entry.className) ? 7.2 : 6.6;
      const w = entry.text.length * perChar + 16;
      const h = 18;
      // System labels sit to the right of their marker; the rest are centred.
      const left = /is-(segmentum|region|era|warp|sector|event)/.test(entry.className || '') ? sx - w / 2 : sx + 10;
      const box = [left, sy - h / 2, left + w, sy + h / 2];
      if (boxes.some((b) => box[0] < b[2] && box[2] > b[0] && box[1] < b[3] && box[3] > b[1])) continue;
      boxes.push(box);
      accepted.push(entry);
      if (accepted.length >= 70) break;
    }
    return accepted;
  }
}
