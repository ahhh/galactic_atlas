/**
 * Info-card content for every kind of selectable thing.
 *
 * Documented worlds show everything the research corpus records, verbatim,
 * plus the best-guess map position with how it was derived. Generated
 * worlds say plainly that they were invented to fill out their system.
 */

import {
  FACTIONS, ERAS, PLACEMENT_LABELS, CONFIDENCE_LABELS, SEGMENTUM_NOTES,
  formatGalactic, formatKly, titleCase,
} from './constants.js';
import { biomeSwatch } from './planet-view.js';
import { featureName } from './navigation.js';

const GENERATED_NOTE = 'This world does not appear in any published source. It was generated to fill out a '
  + 'system the corpus records only one or two bodies in. Its existence, name and every property are invented, '
  + 'following the usual Imperial survey mix: dead worlds and gas giants vastly outnumber inhabited worlds, and '
  + 'hive and forge worlds are rare.';

export class CardBuilder {
  constructor(atlas, actions) {
    this.atlas = atlas;
    this.actions = actions; // { go(target), closeUp(world), era() }
  }

  // --- Worlds -------------------------------------------------------------

  world(world, { mode }) {
    return world.generated ? this._generatedWorld(world, mode) : this._documentedWorld(world, mode);
  }

  _documentedWorld(world, mode) {
    const { atlas } = this;
    const faction = FACTIONS[world.faction] || FACTIONS.unknown;
    const sector = world.sector_id ? atlas.getSector(world.sector_id) : null;
    const subsector = world.subsector_id ? atlas.subsectors.get(world.subsector_id) : null;
    const system = atlas.getSystem(world.system);
    const segmentum = world.segmentum || world.segmentum_estimated;
    const era = this.actions.era();
    const eraInfo = ERAS.find((e) => e.id === era);

    const subtitle = [world.world_type, sector ? sector.name : null, segmentum ? `Segmentum ${segmentum}` : null]
      .filter(Boolean).join(' · ');

    const tags = [
      { text: titleCase(world.location_kind || 'planet') },
      { text: faction.label, tone: 'faction' },
      world.review_state === 'index_only'
        ? { text: 'Index entry only', tone: 'muted' }
        : { text: 'Curated factsheet', tone: 'good' },
    ];

    const go = (target) => () => this.actions.go(target);
    const actions = [];
    if (mode !== 'PLANET_VIEW') actions.push({ label: 'View world close up', primary: true, onClick: () => this.actions.closeUp(world) });
    if (mode !== 'SYSTEM_VIEW' || mode === 'PLANET_VIEW') {
      actions.push({ label: system && system.worlds.length > 1 ? `Open system (${system.worlds.length} bodies)` : 'Open system', onClick: go({ kind: 'system', id: world.system, enter: true, focus: world.id }) });
    }
    if (sector) actions.push({ label: `${sector.name} sector`, onClick: go({ kind: 'sector', id: sector.id }) });
    if (world.source_url) actions.push({ label: 'Source ↗', href: world.source_url });

    // Environment
    const environment = [
      { label: 'Surface / terrain', value: world.surface, wide: true },
      { label: 'Atmosphere / climate', value: world.atmosphere, wide: true },
    ];
    if (world.physical_properties) {
      for (const [key, value] of Object.entries(world.physical_properties)) {
        environment.push({ label: titleCase(key), value: typeof value === 'object' ? JSON.stringify(value) : value });
      }
    }
    if (world.historical_environment) environment.push({ label: 'Historical environment', value: stringify(world.historical_environment), wide: true });
    if (world.environment_evidence) environment.push({ label: 'Evidence', value: humanise(world.environment_evidence) });

    // Significance
    const significance = [{ label: 'Why it matters', value: world.notable, wide: true }];
    for (const note of world.source_notes || []) {
      if (note.note && note.note !== world.notable) significance.push({ label: 'Source note', value: note.note, wide: true, note: note.source });
    }
    for (const primarch of atlas.primarchsByWorld.get(world.id) || []) {
      significance.push({ label: 'Primarch homeworld', value: primarch.name, note: primarch.assignment_note || undefined });
    }
    for (const name of world.primarchs || []) {
      if (!(atlas.primarchsByWorld.get(world.id) || []).some((p) => p.name === name)) {
        significance.push({ label: 'Primarch', value: name });
      }
    }
    for (const entry of atlas.homeworldOf.get(world.id) || []) {
      significance.push({ label: `${entry.faction} homeworld`, value: titleCase(entry.status || ''), note: entry.notes });
    }

    // Era record
    const eraBody = document.createElement('div');
    eraBody.className = 'era-list';
    for (const e of ERAS) {
      const item = document.createElement('div');
      item.className = `era-item${e.id === era ? ' is-current' : ''}`;
      const status = world.era_status?.[e.id] || 'Unknown';
      const events = (world.history || []).filter((h) => h.era === e.id).map((h) => h.event);
      item.innerHTML = '<div class="era-label"></div><div class="era-status"></div>';
      item.children[0].textContent = e.label;
      item.children[1].textContent = status;
      if (/^unknown|not (independently )?established/i.test(status)) item.children[1].classList.add('is-unknown');
      for (const event of events) {
        const ev = document.createElement('div');
        ev.className = 'era-event';
        ev.textContent = event;
        item.appendChild(ev);
      }
      eraBody.appendChild(item);
    }

    // Location
    const location = [
      {
        label: 'Segmentum',
        value: segmentum,
        badge: world.segmentum ? null : 'estimated',
        note: world.segmentum ? world.segmentum_note : 'No segmentum recorded; this is the one the estimated position falls in.',
        onClick: segmentum ? go({ kind: 'segmentum', id: segmentum }) : undefined,
      },
      { label: 'Sector', value: sector ? sector.name : 'Unknown', onClick: sector ? go({ kind: 'sector', id: sector.id }) : undefined, note: world.sector_note },
    ];
    if (subsector) location.push({ label: 'Subsector', value: subsector.name });
    location.push({
      label: 'Star system',
      value: system ? (system.synthetic ? `${system.name} (unnamed star)` : `${system.name} System`) : 'Unknown',
      onClick: go({ kind: 'system', id: world.system, enter: true, focus: world.id }),
      note: system?.synthetic ? 'The corpus names no system for this world. The star and its other bodies are schematic.' : undefined,
    });
    if (world.slot) location.push({ label: 'Orbital position', value: ordinal(world.slot), badge: system?.orbit_order === 'real' ? null : 'schematic' });
    if (world.parent) location.push({ label: 'Orbits', value: atlas.getWorld(world.parent)?.name, onClick: go({ kind: 'world', id: world.parent }) });
    location.push({ label: 'Eye of Terror', value: humanise(world.eye_relation || 'unknown') });
    location.push({
      label: 'Great Rift side',
      value: world.rift_side && world.rift_side !== 'unknown' ? `Imperium ${world.rift_side}` : `Imperium ${world.rift_side_estimated}`,
      badge: world.rift_side && world.rift_side !== 'unknown' ? null : 'estimated',
      note: world.rift_side && world.rift_side !== 'unknown' ? undefined : 'Not recorded; inferred from the estimated position against the schematic Great Rift.',
    });
    if (world.geography_note) location.push({ label: 'Geography note', value: world.geography_note, wide: true });
    if (world.geography_conflict) location.push({ label: 'Geography conflict', value: stringify(world.geography_conflict), wide: true });

    // Placement
    const terra = atlas.frame.terra;
    const placement = world.placement || {};
    const placementFacts = [
      { label: 'Galactic position', value: formatGalactic(world.x, world.y), badge: 'estimated' },
      { label: 'Distance from Terra', value: formatKly(Math.hypot(world.x - terra.x, world.y - terra.y)), badge: 'estimated' },
      { label: 'Method', value: PLACEMENT_LABELS[placement.method] || placement.method },
      { label: 'Confidence', value: CONFIDENCE_LABELS[placement.confidence] || placement.confidence },
    ];
    if (world.placements_by_era) {
      for (const [eraId, p] of Object.entries(world.placements_by_era)) {
        const label = ERAS.find((e) => e.id === eraId)?.short || eraId;
        placementFacts.push({ label: `Recorded location, ${label}`, value: [p.segmentum && `Segmentum ${p.segmentum}`, p.eye_relation && `Eye: ${p.eye_relation}`].filter(Boolean).join(' · ') || 'Unknown' });
      }
    }

    // Identity and research status
    const identity = [];
    for (const alias of world.aliases || []) identity.push({ label: 'Also known as', value: alias });
    for (const alias of atlas.aliasesByName.get(world.name.toLowerCase()) || []) {
      identity.push({ label: 'Possible alias', value: alias.other, note: humanise(alias.relation) });
    }
    if (world.historical_identity) identity.push({ label: 'Historical identity', value: stringify(world.historical_identity), wide: true });
    for (const alt of world.classification_alternates || []) identity.push({ label: 'Also classified as', value: alt });
    if (world.possible_name_collision_note) identity.push({ label: 'Name collision', value: world.possible_name_collision_note, wide: true });
    for (const conflict of atlas.raw.same_name_conflicts || []) {
      if (conflict.name.toLowerCase() === world.name.toLowerCase()) {
        identity.push({ label: 'Same-name conflict', value: `${conflict.classification_1} / ${conflict.classification_2}`, note: conflict.editorial_status, wide: true });
      }
    }

    const research = [
      { label: 'Review state', value: humanise(world.review_state) },
      { label: 'Factsheet', value: humanise(world.factsheet_completeness) },
      { label: 'Source tier', value: world.source_tier, wide: true },
      { label: 'Time scope', value: humanise(world.time_scope) },
    ];
    if (world.planetary_body_confidence) research.push({ label: 'Body type', value: world.planetary_body_confidence, wide: true });
    const sources = new Set([world.source_url, world.source_list_url, ...(world.indexed_attestations || [])].filter(Boolean));
    const sourceBody = linkList(Array.from(sources));

    return {
      kindLabel: `${titleCase(world.location_kind || 'world')} · Documented`,
      title: world.name,
      subtitle,
      accent: faction.color,
      tags,
      actions,
      visual: preview(world),
      groups: [
        { title: 'Classification', facts: [
          { label: 'World type', value: world.world_type },
          { label: 'Allegiance', value: world.affiliation, wide: true, note: 'Historical claims may differ by era.' },
          { label: 'Faction', value: faction.label },
        ] },
        { title: 'Environment', facts: environment },
        { title: 'Significance', facts: significance },
        { title: `Through the ages · now showing ${eraInfo?.short}`, body: eraBody },
        { title: 'Location', facts: location },
        { title: 'Map placement', note: placement.note, facts: placementFacts },
        identity.length ? { title: 'Identity and aliases', facts: identity } : null,
        { title: 'Research status', facts: research },
        { title: 'Sources', body: sourceBody },
      ],
      footer: `Record id ${world.id} · research date ${atlas.raw.research_date || 'unknown'}`,
    };
  }

  _generatedWorld(world, mode) {
    const { atlas } = this;
    const system = atlas.getSystem(world.system);
    const primary = system ? atlas.getWorld(system.primary) : null;
    const sector = world.sector_id ? atlas.getSector(world.sector_id) : null;
    const segmentum = world.segmentum || world.segmentum_estimated;
    const g = 'generated';
    const go = (target) => () => this.actions.go(target);
    const actions = [];
    if (mode !== 'PLANET_VIEW') actions.push({ label: 'View world close up', primary: true, onClick: () => this.actions.closeUp(world) });
    actions.push({ label: `Open ${system?.name || ''} system`, onClick: go({ kind: 'system', id: world.system, enter: true, focus: world.id }) });
    if (primary && primary.id !== world.id && !primary.generated) {
      actions.push({ label: primary.name, onClick: go({ kind: 'world', id: primary.id }) });
    }

    const survey = [
      { label: 'Classification', value: world.class_code ? `${world.world_type} (${world.class_code}-class)` : world.world_type, badge: g },
      { label: 'Population', value: world.population_label, badge: g },
      { label: 'Tithe grade', value: world.tithe_grade, badge: g },
      world.gravity_g ? { label: 'Surface gravity', value: `${world.gravity_g} g`, badge: g }
        : { label: 'Cloud-top gravity', value: `${world.cloudtop_gravity_g} g`, badge: g },
      { label: 'Day length', value: world.tidally_locked && !world.day_hours ? 'Tidally locked' : `${world.day_hours} h`, badge: g },
      { label: 'Mean temperature', value: `${world.mean_temp_c} °C`, badge: g },
      { label: 'Moons', value: world.moons ? String(world.moons) : 'None', badge: g },
    ];
    return {
      kindLabel: `${titleCase(world.location_kind)} · Undocumented`,
      title: world.name,
      subtitle: [world.world_type, system ? `${system.name} system` : null, sector?.name].filter(Boolean).join(' · '),
      accent: '#8d97a6',
      tags: [{ text: 'Generated', tone: 'generated' }, { text: titleCase(world.orbit_zone || '') + ' system' }],
      banner: { tone: 'generated', text: GENERATED_NOTE },
      actions,
      visual: preview(world),
      groups: [
        { title: 'Survey record', facts: survey },
        { title: 'Environment', facts: [
          { label: 'Surface / terrain', value: world.surface, wide: true, badge: g },
          { label: 'Atmosphere', value: world.atmosphere, wide: true, badge: g },
        ] },
        { title: 'Notes', facts: [
          { label: 'Survey note', value: world.notable, wide: true, badge: g },
          { label: 'Allegiance', value: world.affiliation, badge: g },
        ] },
        { title: 'Location', facts: [
          { label: 'Star system', value: system ? `${system.name}` : 'Unknown', onClick: go({ kind: 'system', id: world.system, enter: true, focus: world.id }) },
          { label: 'Orbital position', value: ordinal(world.slot), badge: 'schematic' },
          { label: 'Sector', value: sector?.name || 'Unknown', onClick: sector ? go({ kind: 'sector', id: sector.id }) : undefined },
          { label: 'Segmentum', value: segmentum, badge: world.segmentum ? null : 'estimated' },
          { label: 'Galactic position', value: formatGalactic(world.x, world.y), badge: 'estimated' },
        ] },
      ],
      footer: `Generated record ${world.id}`,
    };
  }

  // --- Systems, sectors, segmenta, features --------------------------------

  system(system, { inSystemView }) {
    const { atlas } = this;
    const worlds = atlas.worldsOf(system.id);
    const primary = atlas.getWorld(system.primary);
    const sectorId = system.sector_id || primary?.sector_id;
    const sector = sectorId ? atlas.getSector(sectorId) : null;
    const documented = worlds.filter((w) => !w.generated);
    const generated = worlds.filter((w) => w.generated);
    const go = (target) => () => this.actions.go(target);

    const strip = (list) => {
      const div = document.createElement('div');
      div.className = 'world-strip';
      for (const world of list) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `world-chip${world.generated ? ' is-generated' : ''}`;
        const swatch = biomeSwatch(world);
        button.innerHTML = '<span class="chip-dot"></span><span></span>';
        button.children[0].style.background = swatch.mid;
        button.children[1].textContent = world.name;
        button.title = world.world_type;
        button.addEventListener('click', go({ kind: 'world', id: world.id, enter: true }));
        div.appendChild(button);
      }
      return div;
    };

    const actions = [];
    if (!inSystemView) actions.push({ label: 'Enter system', primary: true, onClick: go({ kind: 'system', id: system.id, enter: true }) });
    else actions.push({ label: 'Back to galaxy', onClick: go({ kind: 'galaxy-at', id: system.id }) });
    if (primary && !primary.generated) actions.push({ label: primary.name, onClick: go({ kind: 'world', id: primary.id }) });
    if (sector) actions.push({ label: `${sector.name} sector`, onClick: go({ kind: 'sector', id: sector.id }) });
    if (system.source_url) actions.push({ label: 'Source ↗', href: system.source_url });

    return {
      kindLabel: system.free_floating ? 'Free-floating body' : system.synthetic ? 'Star system · unnamed star' : 'Star system · documented',
      title: system.synthetic ? `${system.name} system` : `${system.name} System`,
      subtitle: `${documented.length} documented ${documented.length === 1 ? 'body' : 'bodies'}`
        + (generated.length ? ` · ${generated.length} undocumented` : ''),
      accent: (FACTIONS[system.faction] || FACTIONS.unknown).color,
      actions,
      groups: [
        { title: 'Documented bodies', body: strip(documented), note: documented.length ? null : 'The corpus names this system but records none of its bodies.' },
        generated.length ? { title: 'Undocumented bodies (generated)', body: strip(generated),
          note: 'Generated to fill out the system. Not from any source.' } : null,
        { title: 'Star', facts: system.free_floating ? [{ label: 'Star', value: 'None: this body is not bound to a star' }] : [
          { label: 'Type', value: system.star.label, badge: system.star.schematic ? 'schematic' : null },
          { label: 'Orbit order', value: system.orbit_order === 'real' ? 'Real order' : 'Schematic order', badge: system.orbit_order === 'real' ? null : 'schematic' },
        ] },
        { title: 'Location', facts: [
          { label: 'Sector', value: sector?.name || 'Unknown', onClick: sector ? go({ kind: 'sector', id: sector.id }) : undefined },
          { label: 'Segmentum', value: primary ? atlas.segmentumOf(primary) : null, badge: primary?.segmentum ? null : 'estimated' },
          { label: 'Galactic position', value: formatGalactic(system.x, system.y), badge: 'estimated' },
          { label: 'Placement', value: PLACEMENT_LABELS[system.placement?.method] || '—', note: system.placement?.note },
        ] },
      ],
    };
  }

  sector(sector) {
    const { atlas } = this;
    const worlds = (atlas.worldsBySector.get(sector.id) || []).filter((w) => !w.generated)
      .sort((a, b) => (b.prominence - a.prominence) || a.name.localeCompare(b.name));
    const subs = Array.from(atlas.subsectors.values()).filter((s) => s.sector_id === sector.id);
    const strip = document.createElement('div');
    strip.className = 'world-strip';
    for (const world of worlds) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'world-chip';
      button.innerHTML = '<span class="chip-dot"></span><span></span>';
      button.children[0].style.background = biomeSwatch(world).mid;
      button.children[1].textContent = world.name;
      button.title = world.world_type;
      button.addEventListener('click', () => this.actions.go({ kind: 'world', id: world.id }));
      strip.appendChild(button);
    }
    const segmentum = sector.segmentum || sector.segmentum_estimated;
    return {
      kindLabel: `${titleCase(sector.category || 'sector')}`,
      title: sector.name,
      subtitle: segmentum ? `Segmentum ${segmentum}` : 'Segmentum unknown',
      actions: sector.source ? [{ label: 'Source ↗', href: sector.source }] : [],
      groups: [
        { title: `Documented worlds (${worlds.length})`, body: strip, note: worlds.length ? null : 'No worlds in the corpus are assigned to this sector yet.' },
        subs.length ? { title: 'Subsectors and subregions', facts: subs.map((s) => ({ label: s.name, value: humanise(s.review_state || '') })) } : null,
        { title: 'Classification', facts: [
          { label: 'Category', value: titleCase(sector.category || 'sector') },
          { label: 'Segmentum', value: segmentum, badge: sector.segmentum ? null : 'estimated', onClick: segmentum ? () => this.actions.go({ kind: 'segmentum', id: segmentum }) : undefined },
          { label: 'Index confidence', value: humanise(sector.confidence || '') },
          { label: 'Boundary', value: sector.boundary_note || humanise(sector.sector_geometry || 'unknown'), wide: true },
          sector.segmentum_note ? { label: 'Segmentum note', value: sector.segmentum_note, wide: true } : null,
        ].filter(Boolean) },
        { title: 'Map placement', note: sector.placement.note, facts: [
          { label: 'Centre', value: formatGalactic(sector.x, sector.y), badge: 'estimated' },
          { label: 'Drawn radius', value: formatKly(sector.radius), badge: 'schematic' },
          { label: 'Method', value: PLACEMENT_LABELS[sector.placement.method] },
        ] },
      ],
    };
  }

  segmentum(name) {
    const stats = this.atlas.segmentumStats(name);
    const strip = document.createElement('div');
    strip.className = 'world-strip';
    for (const sector of stats.sectors.sort((a, b) => a.name.localeCompare(b.name))) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'world-chip';
      button.textContent = sector.name;
      button.addEventListener('click', () => this.actions.go({ kind: 'sector', id: sector.id }));
      strip.appendChild(button);
    }
    return {
      kindLabel: 'Segmentum',
      title: `Segmentum ${name}`,
      subtitle: SEGMENTUM_NOTES[name],
      groups: [
        { title: 'Charted here', facts: [
          { label: 'Documented worlds', value: stats.documented.toLocaleString(), note: 'Includes worlds whose segmentum is only estimated from their map position.' },
          { label: 'Undocumented (generated) worlds', value: stats.generated.toLocaleString(), badge: 'generated' },
          { label: 'Sectors and regions', value: String(stats.sectors.length) },
        ] },
        { title: 'Sectors and regions', body: strip },
        { title: 'Boundaries', note: 'Segmentum borders are drawn as wedges radiating from the Segmentum Solar around Terra. This is a schematic of the general layout of the published maps, not a boundary tracing.' },
      ],
    };
  }

  feature(id) {
    const notes = {
      eye_of_terror: [
        'The largest warp storm in the galaxy, where real space and the warp overlap. It was born in the Fall of the Aeldari, when the birth of Slaanesh tore open the old Aeldari heartlands.',
        'The Traitor Legions retreated here after the Horus Heresy, and the Cadian Gate held its only stable exit for ten thousand years.',
      ],
      maelstrom: [
        'A large warp storm close to Terra, on the border of Segmentum Solar. Pirates and renegades, among them the Red Corsairs after the Badab War, use it as a refuge.',
      ],
      great_rift: [
        'The Cicatrix Maledictum tore across the galaxy at the end of M41, after the fall of Cadia at the close of the 13th Black Crusade. It splits the Imperium into Imperium Sanctus to the south, which can still see the Astronomican, and Imperium Nihilus to the north, which cannot.',
        'The ribbon on this map is schematic. It is drawn only in the M42 era view.',
      ],
    }[id] || [];
    return {
      kindLabel: 'Warp phenomenon',
      title: featureName(id),
      subtitle: id === 'great_rift' ? 'Era M42' : id === 'eye_of_terror' ? 'Present from the Fall of the Aeldari onwards' : null,
      groups: notes.map((n, i) => ({ title: i === 0 ? 'Overview' : 'History', note: n })),
    };
  }
}

function preview(world) {
  const swatch = biomeSwatch(world);
  const wrapper = document.createElement('div');
  wrapper.className = 'planet-preview';
  const orb = document.createElement('div');
  orb.className = 'planet-orb';
  orb.style.background = `radial-gradient(circle at 32% 28%, ${swatch.hot}, ${swatch.mid} 45%, ${swatch.cold} 75%, #05060a 100%)`;
  if (swatch.glow) orb.style.boxShadow = `0 0 26px -6px ${swatch.glow}, inset -14px -10px 30px rgba(0,0,0,0.6)`;
  const caption = document.createElement('div');
  caption.className = 'planet-preview-caption';
  caption.textContent = swatch.unknown
    ? 'Its world type is unrecorded, so it is drawn in neutral grey rather than given an invented look.'
    : `Appearance interpreted from the world type (${swatch.label.toLowerCase()}). Not canonical art.`;
  wrapper.append(orb, caption);
  return wrapper;
}

function linkList(urls) {
  const list = document.createElement('ul');
  list.className = 'source-list';
  for (const url of urls) {
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = url;
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = decodeURIComponent(url.replace(/^https?:\/\/(www\.)?/, ''));
    li.appendChild(a);
    list.appendChild(li);
  }
  return list;
}

function humanise(value) {
  if (!value) return null;
  return String(value).replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());
}

function stringify(value) {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(stringify).join('; ');
  if (value && typeof value === 'object') return Object.entries(value).map(([k, v]) => `${humanise(k)}: ${stringify(v)}`).join('; ');
  return String(value);
}

function ordinal(n) {
  if (!n) return null;
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return `${n}${s[(v - 20) % 10] || s[v] || s[0]} from the star`;
}
