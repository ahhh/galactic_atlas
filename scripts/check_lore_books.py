#!/usr/bin/env python3
"""
Check every book in lore/books.json against two public catalogues.

Open Library: each title is searched together with its author. A hit whose
title and author both match is recorded as the book's `openlibrary` work
key, and its first publication year is reported next to ours.

Warhammer 40k Fandom wiki: the title, then "Title (Novel)", "(Anthology)"
and "(Novella)", following redirects. A page is kept as the book's `wiki`
field only when its infobox names the same author, so the atlas never
links a character or starship page that happens to share a book's name.

Lexicanum cannot be checked this way (it sits behind a bot wall), so the
atlas links Lexicanum through its search page instead of a guessed URL.

Usage:  python3 scripts/check_lore_books.py [--write]
"""

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS = ROOT / 'lore' / 'books.json'
API = 'https://warhammer40k.fandom.com/api.php'
OPEN_LIBRARY = 'https://openlibrary.org/search.json'
SUFFIXES = ['', ' (Novel)', ' (Anthology)', ' (Novella)', ' (novel)']


def fetch_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'galactic-atlas-lore-check/1.0'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == 3:
                raise
            time.sleep(2 + attempt * 3)


def api(params):
    params = {**params, 'format': 'json', 'formatversion': '2'}
    return fetch_json(f'{API}?{urllib.parse.urlencode(params)}')


def resolve(titles):
    """Map each requested title to its final page title, or None."""
    out = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        data = api({'action': 'query', 'titles': '|'.join(chunk), 'redirects': 1})
        query = data.get('query', {})
        alias = {}
        for n in query.get('normalized', []):
            alias[n['from']] = n['to']
        redirects = {r['from']: r['to'] for r in query.get('redirects', [])}
        present = {p['title'] for p in query.get('pages', []) if not p.get('missing')}
        for title in chunk:
            t = alias.get(title, title)
            t = redirects.get(t, t)
            out[title] = t if t in present else None
    return out


def norm(text):
    return re.sub(r'[^a-z0-9]+', ' ', text.lower().replace('&', 'and')).strip()


def open_library(book):
    surname = re.findall(r"[A-Za-z][A-Za-z.'\-]+", book['author'].split(',')[0].replace(' (ed.)', ''))[-1]
    params = urllib.parse.urlencode({'title': book['title'], 'author': surname, 'limit': 8,
                                     'fields': 'title,author_name,first_publish_year,key'})
    docs = fetch_json(f'{OPEN_LIBRARY}?{params}').get('docs', [])
    want = norm(book['title'])
    for doc in docs:
        if norm(doc.get('title', '')) == want and any(surname.lower() in a.lower() for a in doc.get('author_name', [])):
            return doc
    return None


def wikitext(title):
    data = api({'action': 'parse', 'page': title, 'prop': 'wikitext'})
    return data.get('parse', {}).get('wikitext', '')


def infobox_field(text, name):
    m = re.search(rf'\|\s*{name}\s*=\s*(.+)', text, re.I)
    if not m:
        return None
    value = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', m.group(1))
    value = re.sub(r'<[^>]+>|\{\{[^}]*\}\}', '', value)
    return value.strip() or None


def main():
    write = '--write' in sys.argv
    books = json.loads(BOOKS.read_text(encoding='utf-8'))
    candidates = []
    for book in books.values():
        base = book.get('wiki') or book['title']
        candidates += [base + s for s in SUFFIXES]
    resolved = resolve(list(dict.fromkeys(candidates)))

    problems = 0
    for bid, book in books.items():
        base = book.get('wiki') or book['title']
        doc = open_library(book)
        if doc:
            book['openlibrary'] = doc['key']
            year = doc.get('first_publish_year')
            ol = f'ok  ({year})' if not book.get('year') or year == book['year'] else f'YEAR? ours {book["year"]}, OL {year}'
        else:
            book.pop('openlibrary', None)
            ol = 'not found'

        page = None
        for suffix in [' (Novel)', ' (Anthology)', ' (Novella)', ' (novel)', '']:
            if resolved.get(base + suffix):
                page = resolved[base + suffix]
                break
        wiki = 'none'
        book.pop('wiki', None)
        if page:
            text = wikitext(page)
            author = infobox_field(text, 'author') or infobox_field(text, 'authors')
            words = re.findall(r'[A-Za-z\-]{4,}', book['author'].lower())
            if author and (any(w in author.lower() for w in words) or author.lower() == 'various'):
                book['wiki'] = page
                wiki = page
        if not doc and wiki == 'none':
            problems += 1
        print(f'{bid:45} OL: {ol:22} wiki: {wiki}')

    print(f'\n{len(books)} books, {problems} to review')
    if write:
        BOOKS.write_text(json.dumps(books, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(f'Wrote {BOOKS.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
