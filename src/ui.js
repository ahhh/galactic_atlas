/**
 * The cogitator interface: world browser, filters, info card, breadcrumbs
 * and status bar. All DOM lives here; this module never touches Three.js.
 *
 * The rule carried over from the research corpus: a value nobody recorded
 * must not look like one somebody did. Estimated positions carry an
 * "Estimated" badge, generated worlds a "Generated" badge, and unrecorded
 * values are shown dimmed.
 */

import { FACTIONS } from './constants.js';
import { biomeSwatch } from './planet-view.js';

const LIST_LIMIT = 300;
const UNKNOWN_PATTERN = /^(unknown|unspecified|not (consistently|documented)|none recorded|—)/i;

const BADGES = {
  estimated: 'Estimated',
  generated: 'Generated',
  recorded: 'Recorded',
  interpreted: 'Interpreted',
  schematic: 'Schematic',
};

export function factRow(fact) {
  const row = document.createElement('div');
  row.className = `fact${fact.wide ? ' is-wide' : ''}`;
  const label = document.createElement('div');
  label.className = 'fact-label';
  label.textContent = fact.label;
  const value = document.createElement('div');
  value.className = 'fact-value';
  const text = fact.value === null || fact.value === undefined || fact.value === '' ? 'Unknown' : String(fact.value);
  if (fact.link) {
    const a = document.createElement('a');
    a.href = fact.link;
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = text;
    value.appendChild(a);
  } else if (fact.onClick) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'inline-link';
    button.textContent = text;
    button.addEventListener('click', fact.onClick);
    value.appendChild(button);
  } else {
    value.textContent = text;
  }
  if (UNKNOWN_PATTERN.test(text)) value.classList.add('is-unknown');
  if (fact.badge) {
    const badge = document.createElement('span');
    badge.className = `badge badge-${fact.badge}`;
    badge.textContent = BADGES[fact.badge] || fact.badge;
    value.appendChild(badge);
  }
  row.append(label, value);
  if (fact.note) {
    const note = document.createElement('div');
    note.className = 'fact-note';
    note.textContent = fact.note;
    row.appendChild(note);
  }
  return row;
}

export class UI {
  constructor(elements, handlers) {
    this.el = elements;
    this.handlers = handlers;
    this.filters = {
      query: '', records: 'documented', segmentum: '', sector: '', faction: '', biome: '',
      kind: '', confidence: '', sort: 'name', showOnMap: false,
    };
    this._bind();
  }

  _bind() {
    const { searchInput, searchResults } = this.el;
    let debounce = null;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => this.handlers.onSearch(searchInput.value), 90);
    });
    searchInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') searchResults.querySelector('.result')?.click();
      if (event.key === 'Escape') {
        searchInput.value = '';
        this.renderSearchResults([]);
      }
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === '/' && document.activeElement !== searchInput) {
        event.preventDefault();
        searchInput.focus();
      }
    });
    for (const button of this.el.tabButtons) {
      button.addEventListener('click', () => this.setTab(button.dataset.tab));
    }
    for (const [key, element] of Object.entries(this.el.filterControls)) {
      const event = element.type === 'checkbox' ? 'change' : 'input';
      element.addEventListener(event, () => {
        this.filters[key] = element.type === 'checkbox' ? element.checked : element.value;
        this.renderList();
      });
    }
    this.el.filterReset.addEventListener('click', () => {
      for (const [key, element] of Object.entries(this.el.filterControls)) {
        if (key === 'sort') continue;
        if (element.type === 'checkbox') element.checked = false;
        else element.value = key === 'records' ? 'documented' : '';
        this.filters[key] = element.type === 'checkbox' ? false : element.value;
      }
      this.renderList();
    });
  }

  setTab(name) {
    for (const button of this.el.tabButtons) button.classList.toggle('is-active', button.dataset.tab === name);
    for (const panel of this.el.tabPanels) panel.classList.toggle('is-active', panel.dataset.tab === name);
  }

  // --- Search ------------------------------------------------------------

  renderSearchResults(results) {
    const container = this.el.searchResults;
    container.textContent = '';
    container.classList.toggle('has-results', results.length > 0);
    for (const result of results) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'result';
      button.innerHTML = `<span class="result-kind kind-${result.code}"></span><span class="result-name"></span><span class="result-secondary"></span>`;
      button.children[0].textContent = result.label;
      button.children[1].textContent = result.name;
      button.children[2].textContent = result.secondary || '';
      button.addEventListener('click', () => {
        this.renderSearchResults([]);
        this.handlers.onNavigate({ kind: result.kind === 'generated' || result.kind === 'primarch' ? 'world' : result.kind, id: result.id });
      });
      container.appendChild(button);
    }
  }

  // --- World browser -----------------------------------------------------

  setAtlas(atlas) {
    this.atlas = atlas;
    this.allWorlds = Array.from(atlas.worlds.values());
    const fill = (select, options) => {
      for (const [value, label] of options) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        select.appendChild(option);
      }
    };
    const c = this.el.filterControls;
    fill(c.segmentum, (atlas.raw.segmenta || []).map((s) => [s, s]));
    fill(c.sector, Array.from(atlas.sectors.values())
      .sort((a, b) => a.name.localeCompare(b.name)).map((s) => [s.id, s.name]));
    fill(c.faction, Object.entries(FACTIONS).map(([key, f]) => [key, f.label]));
    const biomes = new Map();
    for (const world of this.allWorlds) biomes.set(world.biome, biomeSwatch(world).label);
    fill(c.biome, Array.from(biomes.entries()).sort((a, b) => a[1].localeCompare(b[1])));
    const kinds = new Set(this.allWorlds.map((w) => w.location_kind));
    fill(c.kind, Array.from(kinds).sort().map((k) => [k, k.replace(/_/g, ' ')]));
    this.renderList();
  }

  filteredWorlds() {
    const f = this.filters;
    const q = f.query.trim().toLowerCase();
    const out = [];
    for (const world of this.allWorlds) {
      if (f.records === 'documented' && world.generated) continue;
      if (f.records === 'generated' && !world.generated) continue;
      if (q && !world.name.toLowerCase().includes(q) && !(world.world_type || '').toLowerCase().includes(q)
          && !(world.affiliation || '').toLowerCase().includes(q)) continue;
      if (f.segmentum && this.atlas.segmentumOf(world) !== f.segmentum) continue;
      if (f.sector && world.sector_id !== f.sector) continue;
      if (f.faction && world.faction !== f.faction) continue;
      if (f.biome && world.biome !== f.biome) continue;
      if (f.kind && world.location_kind !== f.kind) continue;
      if (f.confidence) {
        const confidence = world.generated ? 'invented' : world.placement?.confidence;
        if (confidence !== f.confidence) continue;
      }
      out.push(world);
    }
    const sectorName = (w) => (w.sector_id ? this.atlas.getSector(w.sector_id)?.name : '') || '~';
    const sorters = {
      name: (a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }),
      notability: (a, b) => (b.prominence || 0) - (a.prominence || 0) || a.name.localeCompare(b.name),
      sector: (a, b) => sectorName(a).localeCompare(sectorName(b)) || a.name.localeCompare(b.name),
      segmentum: (a, b) => (this.atlas.segmentumOf(a) || '~').localeCompare(this.atlas.segmentumOf(b) || '~')
        || a.name.localeCompare(b.name),
      terra: (a, b) => distanceToTerra(a, this.atlas) - distanceToTerra(b, this.atlas),
    };
    out.sort(sorters[f.sort] || sorters.name);
    return out;
  }

  renderList() {
    if (!this.atlas) return;
    const worlds = this.filteredWorlds();
    const total = this.filters.records === 'documented' ? this.atlas.documentedWorlds.length
      : this.filters.records === 'generated' ? this.atlas.generatedCount : this.allWorlds.length;
    this.el.listCount.textContent = worlds.length === total
      ? `${worlds.length.toLocaleString()} worlds`
      : `${worlds.length.toLocaleString()} of ${total.toLocaleString()} worlds`;

    const container = this.el.worldList;
    container.textContent = '';
    const fragment = document.createDocumentFragment();
    for (const world of worlds.slice(0, LIST_LIMIT)) {
      const swatch = biomeSwatch(world);
      const sector = world.sector_id ? this.atlas.getSector(world.sector_id) : null;
      const where = sector ? sector.name : this.atlas.segmentumOf(world) ? `Segmentum ${this.atlas.segmentumOf(world)}` : 'Location unknown';
      const button = document.createElement('button');
      button.type = 'button';
      button.className = `world-row${world.generated ? ' is-generated' : ''}`;
      button.dataset.worldId = world.id;
      button.innerHTML = `
        <span class="world-dot"></span>
        <span class="world-row-body">
          <span class="world-row-name"></span>
          <span class="world-row-meta"><span class="chip chip-type"></span><span class="chip chip-where"></span></span>
        </span>`;
      button.querySelector('.world-dot').style.background =
        `radial-gradient(circle at 35% 30%, ${swatch.hot}, ${swatch.mid} 55%, ${swatch.cold})`;
      button.querySelector('.world-dot').style.boxShadow = `0 0 0 1.5px ${(FACTIONS[world.faction] || FACTIONS.unknown).color}`;
      button.querySelector('.world-row-name').textContent = world.name;
      button.querySelector('.chip-type').textContent = world.world_type || 'Unclassified';
      button.querySelector('.chip-where').textContent = world.generated ? 'Uncharted' : where;
      button.addEventListener('click', () => this.handlers.onNavigate({ kind: 'world', id: world.id }));
      fragment.appendChild(button);
    }
    container.appendChild(fragment);
    if (worlds.length > LIST_LIMIT) {
      const note = document.createElement('p');
      note.className = 'list-note';
      note.textContent = `Showing the first ${LIST_LIMIT}. Search or filter to narrow the list.`;
      container.appendChild(note);
    } else if (!worlds.length) {
      const note = document.createElement('p');
      note.className = 'list-note';
      note.textContent = 'No worlds match these filters.';
      container.appendChild(note);
    }
    if (this._selectedWorld) this.highlightWorld(this._selectedWorld);
    this.handlers.onFilterChange?.(worlds, this.filters.showOnMap && this._filtersActive());
  }

  _filtersActive() {
    const f = this.filters;
    return Boolean(f.query || f.segmentum || f.sector || f.faction || f.biome || f.kind || f.confidence
      || f.records !== 'documented');
  }

  highlightWorld(id) {
    this._selectedWorld = id;
    for (const row of this.el.worldList.querySelectorAll('.world-row')) {
      row.classList.toggle('is-selected', row.dataset.worldId === id);
    }
  }

  // --- Breadcrumbs -------------------------------------------------------

  renderBreadcrumbs(trail) {
    const container = this.el.breadcrumbs;
    container.textContent = '';
    trail.forEach((crumb, index) => {
      if (index > 0) {
        const sep = document.createElement('span');
        sep.className = 'crumb-separator';
        sep.textContent = '›';
        container.appendChild(sep);
      }
      const last = index === trail.length - 1;
      const element = document.createElement(crumb.action && !last ? 'button' : 'span');
      element.className = `crumb${last ? ' is-current' : ''}`;
      element.textContent = crumb.label;
      if (crumb.action && !last) {
        element.type = 'button';
        element.addEventListener('click', () => this.handlers.onNavigate(crumb.action));
      }
      container.appendChild(element);
    });
  }

  // --- Info card ---------------------------------------------------------

  showCard(card) {
    const panel = this.el.inspector;
    panel.textContent = '';
    panel.classList.add('is-open');
    panel.scrollTop = 0;

    const header = document.createElement('header');
    header.className = 'inspector-header';
    header.innerHTML = '<div class="inspector-kind"></div><h2></h2>';
    header.children[0].textContent = card.kindLabel;
    header.children[1].textContent = card.title;
    if (card.accent) header.style.setProperty('--card-accent', card.accent);
    if (card.subtitle) {
      const subtitle = document.createElement('p');
      subtitle.className = 'inspector-subtitle';
      subtitle.textContent = card.subtitle;
      header.appendChild(subtitle);
    }
    if (card.tags?.length) {
      const tags = document.createElement('div');
      tags.className = 'tag-row';
      for (const tag of card.tags) {
        const span = document.createElement('span');
        span.className = `tag${tag.tone ? ` tag-${tag.tone}` : ''}`;
        span.textContent = tag.text;
        tags.appendChild(span);
      }
      header.appendChild(tags);
    }
    panel.appendChild(header);

    if (card.banner) {
      const banner = document.createElement('div');
      banner.className = `banner banner-${card.banner.tone || 'info'}`;
      banner.textContent = card.banner.text;
      panel.appendChild(banner);
    }

    if (card.actions?.length) {
      const actions = document.createElement('div');
      actions.className = 'inspector-actions';
      for (const action of card.actions) {
        const element = document.createElement(action.href ? 'a' : 'button');
        element.className = `action${action.primary ? ' is-primary' : ''}`;
        element.textContent = action.label;
        if (action.href) {
          element.href = action.href;
          element.target = '_blank';
          element.rel = 'noopener';
        } else {
          element.type = 'button';
          element.addEventListener('click', action.onClick);
        }
        actions.appendChild(element);
      }
      panel.appendChild(actions);
    }

    if (card.visual) panel.appendChild(card.visual);

    for (const group of card.groups || []) {
      if (!group) continue;
      const hasContent = group.note || group.body || group.facts?.length;
      if (!hasContent) continue;
      const section = document.createElement('section');
      section.className = 'panel-section';
      const heading = document.createElement('h3');
      heading.textContent = group.title;
      section.appendChild(heading);
      if (group.note) {
        const note = document.createElement('p');
        note.className = 'section-note';
        note.textContent = group.note;
        section.appendChild(note);
      }
      for (const fact of group.facts || []) section.appendChild(factRow(fact));
      if (group.body) section.appendChild(group.body);
      panel.appendChild(section);
    }

    if (card.footer) {
      const footer = document.createElement('footer');
      footer.className = 'inspector-footer';
      footer.textContent = card.footer;
      panel.appendChild(footer);
    }

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'inspector-close';
    close.setAttribute('aria-label', 'Close info card');
    close.textContent = '×';
    close.addEventListener('click', () => this.hideCard());
    panel.appendChild(close);
  }

  hideCard() {
    this.el.inspector.classList.remove('is-open');
    this.el.inspector.textContent = '';
    this.handlers.onCardClosed?.();
  }

  // --- Status bar, loading, toast ---------------------------------------

  updateStatus({ mode, scale, position, era, note }) {
    this.el.statusMode.textContent = mode;
    this.el.statusScale.textContent = scale || '—';
    this.el.statusPosition.textContent = position || '—';
    this.el.statusEra.textContent = era || '—';
    this.el.statusNote.textContent = note || '';
  }

  setLoading(message, progress) {
    if (!message) {
      this.el.loading.classList.add('is-hidden');
      return;
    }
    this.el.loading.classList.remove('is-hidden');
    this.el.loadingMessage.textContent = message;
    this.el.loadingBar.style.width = `${Math.round((progress || 0) * 100)}%`;
  }

  toast(message, duration = 3400) {
    const element = this.el.toast;
    element.textContent = message;
    element.classList.add('is-visible');
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => element.classList.remove('is-visible'), duration);
  }
}

function distanceToTerra(world, atlas) {
  const t = atlas.frame.terra;
  return Math.hypot(world.x - t.x, world.y - t.y);
}
