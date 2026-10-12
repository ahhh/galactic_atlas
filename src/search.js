/**
 * Ranked name search over worlds, systems, sectors, segmenta, warp
 * features, primarchs, and the lore pass's events and books. Documented
 * records rank above generated ones.
 */

const KIND_META = {
  world:     { code: 'w', label: 'World' },
  generated: { code: 'u', label: 'Uncharted' },
  system:    { code: 's', label: 'System' },
  sector:    { code: 'c', label: 'Sector' },
  segmentum: { code: 'g', label: 'Segment.' },
  feature:   { code: 'f', label: 'Warp' },
  primarch:  { code: 'p', label: 'Primarch' },
  event:     { code: 'e', label: 'Event' },
  book:      { code: 'b', label: 'Book' },
};

export class SearchIndex {
  constructor(atlas) {
    this.entries = [];
    const add = (kind, id, name, secondary, boost = 0) => {
      this.entries.push({ kind, id, name, key: normalise(name), secondary, boost, ...KIND_META[kind] });
    };
    for (const world of atlas.worlds.values()) {
      const sector = world.sector_id ? atlas.getSector(world.sector_id) : null;
      const where = sector ? sector.name : (atlas.segmentumOf(world) || '');
      if (world.generated) add('generated', world.id, world.name, world.world_type, -25);
      else add('world', world.id, world.name, [world.world_type, where].filter(Boolean).join(' · '), world.prominence * 4);
      for (const alias of world.aliases || []) add('world', world.id, alias, `alias of ${world.name}`, 0);
    }
    for (const system of atlas.systems.values()) {
      if (system.synthetic) continue;
      add('system', system.id, `${system.name} System`, `${system.worlds.length} bodies`, 6);
    }
    for (const sector of atlas.sectors.values()) {
      add('sector', sector.id, sector.name, sector.category === 'sector' ? (sector.segmentum || 'Sector') : sector.category, 8);
    }
    for (const name of atlas.raw.segmenta || []) add('segmentum', name, `Segmentum ${name}`, 'Segmentum', 14);
    add('feature', 'eye_of_terror', 'Eye of Terror', 'Warp storm', 12);
    add('feature', 'maelstrom', 'Maelstrom', 'Warp storm', 10);
    add('feature', 'great_rift', 'Great Rift (Cicatrix Maledictum)', 'Warp rift · M42', 10);
    for (const primarch of atlas.raw.primarchs || []) {
      const world = primarch.homeworld_id ? atlas.getWorld(primarch.homeworld_id) : null;
      if (world) add('primarch', world.id, primarch.name, `homeworld ${world.name}`, 2);
    }
    for (const event of atlas.chronicle) add('event', event.id, event.name, event.date, 5 + (event.weight || 1) * 2);
    for (const book of atlas.books.values()) {
      add('book', book.id, book.title, book.author, 4);
      if (book.series && book.series !== 'Standalone') add('book', book.id, `${book.series}: ${book.title}`, book.author, -4);
    }
  }

  search(query, limit = 30) {
    const q = normalise(query);
    if (!q) return [];
    const results = [];
    for (const entry of this.entries) {
      let score = 0;
      if (entry.key === q) score = 100;
      else if (entry.key.startsWith(q)) score = 75;
      else if (entry.key.includes(` ${q}`)) score = 55;
      else if (entry.key.includes(q)) score = 35;
      if (!score) continue;
      score += entry.boost - entry.key.length * 0.05;
      results.push({ ...entry, score });
    }
    results.sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
    return results.slice(0, limit);
  }
}

function normalise(text) {
  return String(text).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[’']/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
}
