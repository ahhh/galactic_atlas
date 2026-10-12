/**
 * PLANET_VIEW: one world, close up.
 *
 * There is no canonical imagery for almost any of these worlds. The
 * surface is generated from the recorded world type alone (hive, forge,
 * ice, death world and so on), and the interface says so. A world whose
 * type is unrecorded is rendered in neutral grey rather than given an
 * invented look.
 */

import * as THREE from '../vendor/three.module.js';
import { MODES, hashString } from './constants.js';

const VERTEX = `
  varying vec3 vNormal;
  varying vec3 vPosition;
  varying vec3 vWorldNormal;
  void main() {
    vNormal = normalize(normalMatrix * normal);
    vWorldNormal = normalize(mat3(modelMatrix) * normal);
    vPosition = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const FRAGMENT = `
  precision highp float;
  uniform vec3 uCold; uniform vec3 uMid; uniform vec3 uHot; uniform vec3 uSea;
  uniform vec3 uGlow; uniform vec3 uCloud; uniform vec3 uCity;
  uniform float uSeaLevel; uniform float uIce; uniform float uBanding; uniform float uCityAmount;
  uniform float uGlowAmount; uniform float uCloudAmount; uniform float uSwirl; uniform float uCraters;
  uniform float uSeed; uniform float uTime; uniform vec3 uLight;
  varying vec3 vNormal; varying vec3 vPosition; varying vec3 vWorldNormal;

  vec3 hash3(vec3 p) {
    p = vec3(dot(p, vec3(127.1, 311.7, 74.7)), dot(p, vec3(269.5, 183.3, 246.1)), dot(p, vec3(113.5, 271.9, 124.6)));
    return fract(sin(p) * 43758.5453123) * 2.0 - 1.0;
  }
  float noise(vec3 p) {
    vec3 i = floor(p); vec3 f = fract(p); vec3 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(dot(hash3(i), f), dot(hash3(i + vec3(1,0,0)), f - vec3(1,0,0)), u.x),
                   mix(dot(hash3(i + vec3(0,1,0)), f - vec3(0,1,0)), dot(hash3(i + vec3(1,1,0)), f - vec3(1,1,0)), u.x), u.y),
               mix(mix(dot(hash3(i + vec3(0,0,1)), f - vec3(0,0,1)), dot(hash3(i + vec3(1,0,1)), f - vec3(1,0,1)), u.x),
                   mix(dot(hash3(i + vec3(0,1,1)), f - vec3(0,1,1)), dot(hash3(i + vec3(1,1,1)), f - vec3(1,1,1)), u.x), u.y), u.z);
  }
  float fbm(vec3 p) {
    float t = 0.0; float a = 0.5;
    for (int i = 0; i < 6; i++) { t += noise(p) * a; p *= 2.03; a *= 0.5; }
    return t;
  }
  float ridged(vec3 p) {
    float t = 0.0; float a = 0.5;
    for (int i = 0; i < 4; i++) { t += (1.0 - abs(noise(p))) * a; p *= 2.1; a *= 0.5; }
    return t;
  }

  void main() {
    vec3 unit = normalize(vPosition);
    vec3 sp = unit * 2.6 + vec3(uSeed);
    if (uSwirl > 0.0) {
      float s = uSwirl * (fbm(unit * 1.5 + uTime * 0.02) * 3.0);
      sp += vec3(sin(s + unit.y * 4.0), cos(s), sin(s * 1.3)) * uSwirl;
    }
    float h = fbm(sp) * 0.5 + 0.5;
    float lat = unit.y;
    float bands = sin(lat * 14.0 + fbm(unit * vec3(1.0, 6.0, 1.0) + vec3(uSeed)) * 3.0) * 0.5 + 0.5;
    h = mix(h, bands, uBanding);

    vec3 land = mix(uCold, uMid, smoothstep(0.25, 0.55, h));
    land = mix(land, uHot, smoothstep(0.55, 0.85, h));

    // Impact craters for dead and airless bodies.
    if (uCraters > 0.0) {
      float c = smoothstep(0.62, 0.7, abs(noise(unit * 9.0 + vec3(uSeed))));
      land *= 1.0 - c * 0.35 * uCraters;
    }

    float sea = step(h, uSeaLevel);
    vec3 colour = mix(land, uSea * (0.7 + h), sea * step(0.001, uSeaLevel));

    float ice = smoothstep(1.0 - uIce * 0.45, 1.0 - uIce * 0.3, abs(lat) + (h - 0.5) * 0.2);
    colour = mix(colour, vec3(0.92, 0.95, 1.0), ice * step(0.001, uIce));

    vec3 normal = normalize(vNormal);
    float lambert = dot(normalize(vWorldNormal), normalize(uLight));
    float day = smoothstep(-0.15, 0.45, lambert);

    vec3 lit = colour * (0.05 + day * 1.1);

    // Lava cracks, forge glow or Necron light: veins that glow on both sides.
    if (uGlowAmount > 0.0) {
      float vein = smoothstep(0.86, 0.97, ridged(sp * 1.6));
      lit += uGlow * vein * uGlowAmount * (0.6 + 0.4 * (1.0 - day));
    }
    // City lights on the night side.
    if (uCityAmount > 0.0) {
      float density = smoothstep(0.45, 0.8, fbm(unit * 7.0 + vec3(uSeed * 2.0))) * (1.0 - sea);
      float sparkle = smoothstep(0.2, 0.9, noise(unit * 80.0));
      lit += uCity * density * sparkle * uCityAmount * (1.0 - day) * 1.6;
    }
    // Cloud layer.
    if (uCloudAmount > 0.0) {
      float cloud = smoothstep(0.5, 0.75, fbm(unit * 3.2 + vec3(uTime * 0.01, 0.0, uSeed)) * 0.5 + 0.5);
      lit = mix(lit, uCloud * (0.08 + day), cloud * uCloudAmount);
    }
    float rim = pow(1.0 - abs(dot(normal, vec3(0.0, 0.0, 1.0))), 3.0);
    lit += uCloud * rim * 0.25 * (0.3 + day);
    gl_FragColor = vec4(lit, 1.0);
  }
`;

const GAS_PALETTES = [
  ['#7a5636', '#c49a6c', '#ecd6b0'],
  ['#2d4c7a', '#6a92c4', '#cfe1f2'],
  ['#3d6b6a', '#7fb0a8', '#d7ece4'],
  ['#5a3a52', '#a4708e', '#e6c8d6'],
  ['#6a4a1e', '#b8863e', '#f0d08e'],
];

/** Visual parameters per biome. Colours are [cold, mid, hot]. */
const BIOMES = {
  hive:      { c: ['#2e2d2c', '#56534d', '#8a8478'], sea: 0, city: 1.0, cityColour: '#ffc56a', cloud: 0.35, cloudColour: '#8a7a62', label: 'Hive world' },
  forge:     { c: ['#2a140e', '#62291a', '#9c4a28'], sea: 0, glow: '#ff7a2a', glowAmount: 0.9, city: 0.5, cityColour: '#ff9a4a', cloud: 0.3, cloudColour: '#5a4a44', label: 'Forge world' },
  agri:      { c: ['#3b5524', '#7f9536', '#c9b35a'], sea: 0.32, seaColour: '#1d3c5a', city: 0.12, cloud: 0.4, label: 'Agri world' },
  ice:       { c: ['#8ea6ba', '#c9d9e6', '#f4f8fb'], sea: 0, ice: 1.0, cloud: 0.15, craters: 0.4, label: 'Ice world' },
  desert:    { c: ['#6e4f2c', '#b08552', '#dfc08a'], sea: 0, cloud: 0.06, cloudColour: '#e8cfa0', label: 'Desert world' },
  ocean:     { c: ['#2a5a4a', '#4a7a5a', '#9aa87a'], sea: 0.78, seaColour: '#16406e', cloud: 0.45, label: 'Ocean world' },
  jungle:    { c: ['#0f2c17', '#2b5822', '#5f8a33'], sea: 0.3, seaColour: '#173a3a', cloud: 0.6, label: 'Death / jungle world' },
  feral:     { c: ['#2b4824', '#677a43', '#a99a6a'], sea: 0.5, seaColour: '#1b3e66', ice: 0.35, cloud: 0.5, label: 'Feral / feudal world' },
  temperate: { c: ['#2d4a2a', '#6b7a48', '#ab9f74'], sea: 0.48, seaColour: '#1c4070', ice: 0.3, city: 0.35, cloud: 0.45, label: 'Civilised world' },
  shrine:    { c: ['#5e5036', '#a08c66', '#e4d2a2'], sea: 0.28, seaColour: '#2a3f5a', city: 0.55, cityColour: '#ffd98a', cloud: 0.3, label: 'Shrine world' },
  fortress:  { c: ['#3a4047', '#676f78', '#a1a9b2'], sea: 0.2, seaColour: '#24364a', city: 0.45, cityColour: '#ffe2a8', cloud: 0.25, label: 'Fortress world' },
  mining:    { c: ['#473828', '#6e5842', '#9a8366'], sea: 0, city: 0.2, cloud: 0.1, craters: 0.6, label: 'Mining world' },
  dead:      { c: ['#47474a', '#747477', '#a6a6a8'], sea: 0, craters: 1.0, label: 'Dead world' },
  lava:      { c: ['#160c0a', '#36180e', '#622813'], sea: 0, glow: '#ff5a1a', glowAmount: 1.2, craters: 0.3, label: 'Scorched / molten world' },
  tomb:      { c: ['#1a201e', '#323d38', '#57655d'], sea: 0, glow: '#4dff6a', glowAmount: 0.8, craters: 0.5, label: 'Tomb world' },
  daemon:    { c: ['#2a0a2e', '#6a1450', '#c43a7a'], sea: 0, glow: '#ff3ab0', glowAmount: 0.5, swirl: 1.0, cloud: 0.3, cloudColour: '#b04a9a', label: 'Daemon world' },
  ork:       { c: ['#55361f', '#87582f', '#b58a52'], sea: 0.12, seaColour: '#2f3f2a', cloud: 0.15, cloudColour: '#c8a878', city: 0.1, label: 'Ork world' },
  maiden:    { c: ['#1d5536', '#4c974f', '#b6d488'], sea: 0.55, seaColour: '#1a5a7a', cloud: 0.4, label: 'Maiden world' },
  alien:     { c: ['#26454f', '#577f72', '#adc49c'], sea: 0.35, seaColour: '#2a2a5a', cloud: 0.4, label: 'Xenos world' },
  unknown:   { c: ['#3a3c40', '#5b5d62', '#7c7e84'], sea: 0, cloud: 0, label: 'Unrecorded world type', unknown: true },
};

function paletteFor(world) {
  if (world.biome === 'gas') {
    const palette = GAS_PALETTES[hashString(world.id) % GAS_PALETTES.length];
    return { c: palette, banding: 1, cloud: 0, label: 'Gas giant' };
  }
  return BIOMES[world.biome] || BIOMES.unknown;
}

/** CSS colours for list swatches, the inspector and system view. */
export function biomeSwatch(world) {
  if (['craftworld', 'webway', 'station'].includes(world.biome)) {
    const colours = {
      craftworld: ['#3d4a5a', '#c8d6e0', '#f6f2e6'],
      webway: ['#1e1630', '#5a3f8a', '#b59ae6'],
      station: ['#2c3138', '#6e7782', '#b8c0c8'],
    }[world.biome];
    return { cold: colours[0], mid: colours[1], hot: colours[2], glow: null, label: world.biome };
  }
  const p = paletteFor(world);
  return { cold: p.c[0], mid: p.c[1], hot: p.c[2], glow: p.glow || null, label: p.label, unknown: Boolean(p.unknown) };
}

export class PlanetView {
  constructor(sceneManager) {
    this.scene = sceneManager.scene(MODES.PLANET);
    this.root = new THREE.Group();
    this.scene.add(this.root);
    this.time = 0;
    this.light = new THREE.DirectionalLight(0xffffff, 2.2);
    this.light.position.set(5, 2, 4);
    this.scene.add(this.light);
    this.scene.add(new THREE.AmbientLight(0x8890a0, 0.35));
  }

  clear() {
    for (const child of [...this.root.children]) {
      this.root.remove(child);
      child.traverse((node) => { node.geometry?.dispose(); node.material?.dispose(); });
    }
    this.object = null;
    this.uniforms = null;
  }

  load(world) {
    this.clear();
    if (world.biome === 'craftworld') this.object = buildCraftworld(world);
    else if (world.biome === 'webway') this.object = buildWebwayCity();
    else if (world.biome === 'station') this.object = buildStation();
    else this.object = this._buildPlanet(world);
    this.root.add(this.object);
  }

  _buildPlanet(world) {
    const p = paletteFor(world);
    const colour = (hex) => new THREE.Color(hex);
    this.uniforms = {
      uCold: { value: colour(p.c[0]) },
      uMid: { value: colour(p.c[1]) },
      uHot: { value: colour(p.c[2]) },
      uSea: { value: colour(p.seaColour || '#1c3a5e') },
      uGlow: { value: colour(p.glow || '#000000') },
      uCloud: { value: colour(p.cloudColour || '#e8eef4') },
      uCity: { value: colour(p.cityColour || '#ffd28a') },
      uSeaLevel: { value: p.sea || 0 },
      uIce: { value: p.ice || 0 },
      uBanding: { value: p.banding || 0 },
      uCityAmount: { value: p.city || 0 },
      uGlowAmount: { value: p.glowAmount || 0 },
      uCloudAmount: { value: p.cloud || 0 },
      uSwirl: { value: p.swirl || 0 },
      uCraters: { value: p.craters || 0 },
      uSeed: { value: (hashString(world.id) % 1000) / 37 },
      uTime: { value: 0 },
      uLight: { value: new THREE.Vector3(1, 0.3, 0.7).normalize() },
    };
    const mesh = new THREE.Mesh(
      new THREE.SphereGeometry(1, 160, 120),
      new THREE.ShaderMaterial({ uniforms: this.uniforms, vertexShader: VERTEX, fragmentShader: FRAGMENT }),
    );
    const group = new THREE.Group();
    group.add(mesh);
    if (p.cloud > 0.2 || world.biome === 'gas' || world.biome === 'daemon') {
      const haze = new THREE.Mesh(
        new THREE.SphereGeometry(1.04, 64, 48),
        new THREE.MeshBasicMaterial({
          color: colour(p.cloudColour || '#9ec4ff'), transparent: true, opacity: 0.12,
          side: THREE.BackSide, blending: THREE.AdditiveBlending, depthWrite: false,
        }),
      );
      group.add(haze);
    }
    group.rotation.z = 0.35;
    this.spin = mesh;
    return group;
  }

  update(delta) {
    this.time += delta;
    if (this.uniforms) this.uniforms.uTime.value = this.time;
    if (this.spin) this.spin.rotation.y += delta * 0.06;
    else if (this.object) this.object.rotation.y += delta * 0.08;
  }
}

/** Models for bodies that are not planets; null for ordinary worlds. */
export function specialModel(world) {
  if (world.biome === 'craftworld') return buildCraftworld(world);
  if (world.biome === 'webway') return buildWebwayCity();
  if (world.biome === 'station') return buildStation();
  return null;
}

function buildCraftworld(world) {
  const group = new THREE.Group();
  const bone = new THREE.MeshStandardMaterial({ color: 0xf1ead8, roughness: 0.45, metalness: 0.1 });
  const accentHue = (hashString(world.id) % 360) / 360;
  const accent = new THREE.MeshStandardMaterial({
    color: new THREE.Color().setHSL(accentHue, 0.6, 0.5), roughness: 0.3, metalness: 0.3,
    emissive: new THREE.Color().setHSL(accentHue, 0.7, 0.25), emissiveIntensity: 0.6,
  });
  const dome = new THREE.MeshPhysicalMaterial({
    color: 0xbfe6ff, transparent: true, opacity: 0.35, roughness: 0.05, transmission: 0.4,
  });
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.65, 0.18, 48), bone);
  group.add(hub);
  const hubDome = new THREE.Mesh(new THREE.SphereGeometry(0.45, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2), dome);
  hubDome.position.y = 0.09;
  group.add(hubDome);
  const arms = 5 + (hashString(world.id) % 3);
  for (let i = 0; i < arms; i += 1) {
    const a = (i / arms) * Math.PI * 2;
    const length = 1.1 + ((hashString(world.id + i) % 100) / 100) * 0.7;
    const arm = new THREE.Mesh(new THREE.BoxGeometry(length, 0.06, 0.12), bone);
    arm.position.set(Math.cos(a) * (0.55 + length / 2), 0, Math.sin(a) * (0.55 + length / 2));
    arm.rotation.y = -a;
    group.add(arm);
    const pod = new THREE.Mesh(new THREE.SphereGeometry(0.16, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), dome);
    pod.position.set(Math.cos(a) * (0.6 + length), 0.03, Math.sin(a) * (0.6 + length));
    group.add(pod);
    const spire = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.6, 12), accent);
    spire.position.set(Math.cos(a) * 0.9, 0.3, Math.sin(a) * 0.9);
    group.add(spire);
  }
  const central = new THREE.Mesh(new THREE.ConeGeometry(0.08, 1.4, 16), accent);
  central.position.y = 0.7;
  group.add(central);
  group.rotation.x = 0.5;
  return group;
}

function buildWebwayCity() {
  const group = new THREE.Group();
  const material = new THREE.MeshStandardMaterial({ color: 0x2a2140, roughness: 0.4, metalness: 0.6, emissive: 0x3b1c6a, emissiveIntensity: 0.5 });
  for (let i = 0; i < 40; i += 1) {
    const h = 0.4 + ((i * 37) % 17) / 10;
    const spire = new THREE.Mesh(new THREE.ConeGeometry(0.04 + (i % 3) * 0.02, h, 6), material);
    const a = i * 2.399;
    const r = 0.15 + (i % 7) * 0.12;
    spire.position.set(Math.cos(a) * r, h / 2 - 0.6, Math.sin(a) * r);
    group.add(spire);
  }
  const ring = new THREE.Mesh(new THREE.TorusGeometry(1.3, 0.03, 8, 96), new THREE.MeshBasicMaterial({ color: 0xb59ae6 }));
  ring.rotation.x = Math.PI / 2;
  group.add(ring);
  return group;
}

function buildStation() {
  const group = new THREE.Group();
  const hull = new THREE.MeshStandardMaterial({ color: 0x7a7f86, roughness: 0.7, metalness: 0.5 });
  const gold = new THREE.MeshStandardMaterial({ color: 0xb8913d, roughness: 0.4, metalness: 0.8 });
  const spine = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, 2.2, 16), hull);
  group.add(spine);
  for (const y of [-0.6, 0, 0.6]) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.55 + Math.abs(y) * 0.3, 0.06, 10, 48), y === 0 ? gold : hull);
    ring.position.y = y;
    ring.rotation.x = Math.PI / 2;
    group.add(ring);
  }
  const spire = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.7, 16), gold);
  spire.position.y = 1.45;
  group.add(spire);
  group.rotation.z = 0.3;
  return group;
}
