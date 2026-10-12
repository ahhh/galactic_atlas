/**
 * Lore building blocks: event kinds, and the DOM for timelines, book lists
 * and lore write-ups. Shared by the info cards and the Lore and Books tabs.
 *
 * Lore is paraphrased background, not research-corpus data, so it is drawn
 * in its own voice (a serif reading face) and never mixed into the
 * fact rows that carry recorded/estimated badges.
 */

export const EVENT_KINDS = {
  crusade:     { label: 'Crusade',     color: '#e3bf6a' },
  heresy:      { label: 'Heresy',      color: '#c04fd8' },
  war:         { label: 'War',         color: '#d2483f' },
  xenos:       { label: 'Xenos war',   color: '#62c36b' },
  disaster:    { label: 'Catastrophe', color: '#e8833a' },
  founding:    { label: 'Founding',    color: '#6aa6d8' },
  inquisition: { label: 'Inquisition', color: '#e48c74' },
  era:         { label: 'Age',         color: '#a59d8b' },
};

export function eventKind(event) {
  return EVENT_KINDS[event.kind] || EVENT_KINDS.era;
}

/** Epithet and paragraphs of a world, sector or feature write-up. */
export function loreProse(entry) {
  const wrapper = document.createElement('div');
  wrapper.className = 'lore-prose';
  if (entry.epithet) {
    const epithet = document.createElement('p');
    epithet.className = 'lore-epithet';
    epithet.textContent = entry.epithet;
    wrapper.appendChild(epithet);
  }
  const paragraphs = Array.isArray(entry.overview) ? entry.overview : [entry.overview || entry.summary].filter(Boolean);
  for (const text of paragraphs) {
    const p = document.createElement('p');
    p.textContent = text;
    wrapper.appendChild(p);
  }
  return wrapper;
}

/**
 * A vertical timeline of events. `compact` drops the summaries (for long
 * lists); `current` marks one event as the one being shown.
 */
export function eventTimeline(events, { onSelect, compact = false, current = null, ages = null } = {}) {
  const list = document.createElement('ol');
  list.className = `lore-timeline${compact ? ' is-compact' : ''}`;
  let lastAge = null;
  for (const event of events) {
    if (ages && event.age !== lastAge) {
      lastAge = event.age;
      const age = ages.find((a) => a.id === event.age);
      const heading = document.createElement('li');
      heading.className = 'lore-age';
      heading.innerHTML = '<span class="lore-age-name"></span><span class="lore-age-blurb"></span>';
      heading.children[0].textContent = age?.name || '';
      heading.children[1].textContent = age?.blurb || '';
      list.appendChild(heading);
    }
    const kind = eventKind(event);
    const item = document.createElement('li');
    item.className = `lore-event${event.id === current ? ' is-current' : ''}`;
    item.style.setProperty('--kind', kind.color);
    item.dataset.eventId = event.id;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'lore-event-button';
    button.innerHTML = '<span class="lore-event-date"></span><span class="lore-event-name"></span>';
    button.children[0].textContent = event.date;
    button.children[1].textContent = event.name;
    if (onSelect) button.addEventListener('click', () => onSelect(event));
    else button.disabled = true;
    item.appendChild(button);
    if (!compact) {
      const summary = document.createElement('p');
      summary.className = 'lore-event-summary';
      summary.textContent = firstSentence(event.summary);
      item.appendChild(summary);
    }
    list.appendChild(item);
  }
  return list;
}

/** A list of books, each opening its own card. */
export function bookList(books, { onSelect, showSeries = true } = {}) {
  const list = document.createElement('ul');
  list.className = 'book-list';
  for (const book of books) {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'book-row';
    button.innerHTML = '<span class="book-spine"></span><span class="book-body"><span class="book-title"></span><span class="book-meta"></span></span>';
    button.querySelector('.book-spine').style.setProperty('--spine', spineColour(book.series));
    button.querySelector('.book-title').textContent = book.title;
    button.querySelector('.book-meta').textContent = [book.author, showSeries ? seriesLabel(book) : null, book.year]
      .filter(Boolean).join(' · ');
    if (onSelect) button.addEventListener('click', () => onSelect(book));
    item.appendChild(button);
    list.appendChild(item);
  }
  return list;
}

/** External links for a book, as action-button specs. */
export function bookLinks(book) {
  return (book.links || []).map((link) => ({ label: `${link.label} ↗`, href: link.url }));
}

export function seriesLabel(book) {
  if (!book.series || book.series === 'Standalone') return null;
  return book.number ? `${book.series} #${book.number}` : book.series;
}

function firstSentence(text) {
  if (!text) return '';
  const match = text.match(/^.*?[.!?](\s|$)/);
  return match ? match[0].trim() : text;
}

/** A stable, muted colour per series so the spines of a series match. */
function spineColour(series) {
  let h = 0;
  for (const c of series || '') h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return `hsl(${h % 360} 38% 46%)`;
}
