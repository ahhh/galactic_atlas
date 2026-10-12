/**
 * The atlas catalogue: loads data/atlas.json and indexes it.
 *
 * Every world, documented or generated, has a best-guess galactic position
 * assigned by scripts/build_atlas.py, together with the method and
 * confidence of that guess. Nothing here invents further data.
 */

import { FACTIONS } from './constants.js';

export class Atlas {
  constructor() {
    this.worlds = new Map();
    this.systems = new Map();
    this.sectors = new Map();
    this.subsectors = new Map();
    this.worldsBySector = new Map();
    this.systemsBySector = new Map();
    this.primarchsByWorld = new Map();
    this.homeworldOf = new Map();
    this.aliasesByName = new Map();
  }

  async load(onProgress = () => {}) {
    onProgress('Consulting the Astronomican…', 0.1);
    const response = await fetch('data/atlas.json');
    if (!response.ok) throw new Error(`data/atlas.json: HTTP ${response.status}`);
    onProgress('Decoding star charts…', 0.55);
    const data = await response.json();
    this.raw = data;
    this.frame = data.frame;
    this.features = data.features;

    for (const sector of data.sectors) this.sectors.set(sector.id, sector);
    for (const sub of data.subsectors) this.subsectors.set(sub.id, sub);
    for (const system of data.systems) this.systems.set(system.id, system);
    for (const world of data.worlds) {
      this.worlds.set(world.id, world);
      if (world.sector_id) push(this.worldsBySector, world.sector_id, world);
    }
    for (const system of data.systems) {
      const primary = this.worlds.get(system.primary);
      system.faction = primary ? primary.faction : 'unknown';
      system.documentedCount = system.worlds.filter((id) => !this.worlds.get(id)?.generated).length;
      const sectorId = system.sector_id || primary?.sector_id;
      if (sectorId) push(this.systemsBySector, sectorId, system);
    }
    for (const primarch of data.primarchs || []) {
      if (primarch.homeworld_id) push(this.primarchsByWorld, primarch.homeworld_id, primarch);
    }
    for (const entry of data.faction_homeworlds || []) {
      const world = this.findWorldByName(entry.main_world);
      if (world) push(this.homeworldOf, world.id, entry);
    }
    for (const alias of data.aliases || []) {
      push(this.aliasesByName, alias.a.toLowerCase(), { other: alias.b, relation: alias.relation });
      push(this.aliasesByName, alias.b.toLowerCase(), { other: alias.a, relation: alias.relation });
    }
    this.documentedWorlds = data.worlds.filter((w) => !w.generated);
    this.generatedCount = data.worlds.length - this.documentedWorlds.length;
    onProgress('Charts ready', 1);
  }

  getWorld(id) { return this.worlds.get(id) || null; }
  getSystem(id) { return this.systems.get(id) || null; }
  getSector(id) { return this.sectors.get(id) || null; }

  findWorldByName(name) {
    if (!name) return null;
    const needle = name.toLowerCase();
    for (const world of this.documentedWorlds || this.worlds.values()) {
      if (world.name.toLowerCase() === needle) return world;
    }
    return null;
  }

  worldsOf(systemId) {
    const system = this.getSystem(systemId);
    return system ? system.worlds.map((id) => this.worlds.get(id)).filter(Boolean) : [];
  }

  /** The recorded segmentum, or the one the estimated position falls in. */
  segmentumOf(world) {
    return world.segmentum || world.segmentum_estimated || null;
  }

  factionOf(world) {
    return FACTIONS[world.faction] || FACTIONS.unknown;
  }

  segmentumStats(name) {
    let documented = 0;
    let generated = 0;
    const sectors = [];
    for (const world of this.worlds.values()) {
      if (this.segmentumOf(world) !== name) continue;
      if (world.generated) generated += 1; else documented += 1;
    }
    for (const sector of this.sectors.values()) {
      if ((sector.segmentum || sector.segmentum_estimated) === name) sectors.push(sector);
    }
    return { documented, generated, sectors };
  }
}

function push(map, key, value) {
  if (!map.has(key)) map.set(key, []);
  map.get(key).push(value);
}
