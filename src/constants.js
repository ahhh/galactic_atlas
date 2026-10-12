/**
 * Shared vocabulary: view modes, faction colours, era definitions and
 * number/coordinate formatting.
 *
 * Galactic coordinates are thousands of light years (kly) on a flat plane,
 * galactic core at the origin, x to galactic east and y to galactic north.
 * In the 3D scene the plane is XZ with north towards -Z, so the default
 * top-down camera shows north at the top of the screen.
 */

export const MODES = {
  GALAXY: 'GALAXY_VIEW',
  SYSTEM: 'SYSTEM_VIEW',
  PLANET: 'PLANET_VIEW',
};

export const FACTIONS = {
  imperium:   { label: 'Imperium',           color: '#e3bf6a' },
  mechanicus: { label: 'Adeptus Mechanicus', color: '#e0623f' },
  chaos:      { label: 'Chaos',              color: '#c04fd8' },
  aeldari:    { label: 'Aeldari',            color: '#53d6d0' },
  drukhari:   { label: 'Drukhari',           color: '#7a6cf0' },
  necrons:    { label: 'Necrons',            color: '#62e36b' },
  orks:       { label: 'Orks',               color: '#9fb83a' },
  tau:        { label: "T'au Empire",        color: '#5aa7f0' },
  tyranids:   { label: 'Tyranids',           color: '#e05a8a' },
  contested:  { label: 'Contested',          color: '#c79b6c' },
  unknown:    { label: 'Unknown / unclaimed', color: '#8d97a6' },
};

export const ERAS = [
  { id: 'pre_eye', short: 'Pre-Fall', label: 'Before the Fall of the Aeldari', eye: false, rift: false },
  { id: 'pre_rift', short: 'M41', label: 'M41 · Eye of Terror, before the Great Rift', eye: true, rift: false },
  { id: 'post_rift', short: 'M42', label: 'M42 · Eye of Terror and Great Rift', eye: true, rift: true },
];

export const PLACEMENT_LABELS = {
  anchor: 'Hand-placed from published maps',
  lore: 'Placed from how the lore describes it',
  system: 'Shares a star system',
  subsector: 'Inside its recorded subsector',
  sector: 'Inside its recorded sector',
  hint: 'From a place name in its notes',
  segmentum: 'Random within its segmentum',
  faction: 'Random within its faction’s region',
  random: 'Random (no location data)',
  generated: 'Generated with its system',
};

export const CONFIDENCE_LABELS = {
  approximate: 'Approximate',
  guess: 'Best guess',
  invented: 'Invented',
};

export const SEGMENTUM_NOTES = {
  Solar: 'The heart of the Imperium, centred on Terra. Its fortress is Mars.',
  Obscurus: 'Galactic north. It holds the Eye of Terror, the Cadian Gate and the galactic core. Its fortress is Cypra Mundi.',
  Ultima: 'The largest segmentum, stretching east to the Eastern Fringe. It holds Ultramar, Baal and the T’au frontier. Its fortress is Kar Duniash.',
  Pacificus: 'Galactic west. Its fortress is Hydraphur.',
  Tempestus: 'Galactic south. Its fortress is Bakka.',
};

/** Map-plane coordinates (kly) to a scene position. */
export function toScene(x, y, z = 0) {
  return { x, y: z, z: -y };
}

export function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  const abs = Math.abs(value);
  if (abs !== 0 && (abs >= 1e6 || abs < 10 ** -digits)) return value.toExponential(2);
  return value.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 });
}

export function formatKly(kly) {
  if (kly < 1) return `${formatNumber(kly * 1000, 0)} ly`;
  return `${formatNumber(kly, 1)} kly`;
}

/** "12.3 kly E, 4.1 kly S" relative to the galactic core. */
export function formatGalactic(x, y) {
  const ew = `${formatNumber(Math.abs(x), 1)} kly ${x >= 0 ? 'E' : 'W'}`;
  const ns = `${formatNumber(Math.abs(y), 1)} kly ${y >= 0 ? 'N' : 'S'}`;
  return `${ew}, ${ns}`;
}

export function titleCase(text) {
  return String(text).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/** FNV-1a; stable per-id variety for schematic visuals. */
export function hashString(text) {
  let h = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}
