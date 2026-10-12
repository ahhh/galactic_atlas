#!/usr/bin/env python3
"""
Build data/atlas.json for the web atlas from the research database.

The research database (atlas_data.json) deliberately records no map
coordinates: no canonical, consistently projected galactic coordinates
exist for Warhammer 40,000. The web atlas still needs somewhere to draw
every world, so this script assigns each one a *best-guess* position and
records exactly how that guess was made. Nothing here is written back to
the research database.

Placement precedence (first rule that applies wins):

  1. anchor      hand-placed approximation from the published galaxy maps
  2. system      shares a star system with an anchored or placed system
  3. subsector   scattered inside its subsector, inside its sector
  4. sector      scattered inside its sector's approximate footprint
  5. hint        a place name in the record's notes (e.g. "Ultramar")
  6. segmentum   random point inside the recorded segmentum's wedge
  7. faction     random point in the region that faction is known to hold
  8. random      random point in Imperial space

Randomness is seeded from each record's id, so builds are reproducible.

Frame: a flat galactic plane in thousands of light years (kly), galactic
core at the origin, x towards galactic east, y towards galactic north.

Usage:  python3 scripts/build_atlas.py
"""

import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'atlas_data.json'
OUTPUT = ROOT / 'data' / 'atlas.json'

# --- Galactic frame ---------------------------------------------------------

GALAXY_RADIUS = 50.0
TERRA = (-6.0, -10.0)
SOLAR_RADIUS = 8.0

# Segmentum wedges, as compass bearings measured anticlockwise from galactic
# east around Terra, outside the Segmentum Solar circle.
WEDGES = {
    'Ultima': (-60.0, 45.0),
    'Obscurus': (45.0, 150.0),
    'Pacificus': (150.0, 225.0),
    'Tempestus': (225.0, 300.0),
}

EYE_OF_TERROR = {'x': -24.0, 'y': 16.0, 'r': 4.5}
MAELSTROM = {'x': 0.0, 'y': -4.0, 'r': 1.6}

# The Cicatrix Maledictum, west to east. Schematic, not a boundary tracing.
GREAT_RIFT = [
    (-24, 16), (-16, 11), (-8, 6.5), (0, 4.5), (8, 2.5), (16, 1),
    (24, -1), (32, -3), (40, -3), (47, -1),
]

# Named regions that are drawn as map labels only.
REGION_LABELS = [
    {'name': 'Galactic Core', 'x': 0.0, 'y': 0.0, 'kind': 'region'},
    {'name': 'Eastern Fringe', 'x': 47.0, 'y': -24.0, 'kind': 'region'},
    {'name': 'Halo Stars', 'x': -4.0, 'y': 48.0, 'kind': 'region'},
    {'name': 'Koronus Expanse', 'x': -2.0, 'y': 44.0, 'kind': 'region'},
    {'name': 'Ghoul Stars', 'x': 44.0, 'y': 26.0, 'kind': 'region'},
    {'name': 'Damocles Gulf', 'x': 40.5, 'y': -15.5, 'kind': 'region'},
    {'name': "T'au Empire", 'x': 46.0, 'y': -13.0, 'kind': 'realm'},
    {'name': 'Ultramar', 'x': 34.0, 'y': -20.5, 'kind': 'realm'},
    {'name': 'Imperium Nihilus', 'x': 12.0, 'y': 20.0, 'kind': 'era', 'era': 'post_rift'},
    {'name': 'Imperium Sanctus', 'x': 10.0, 'y': -26.0, 'kind': 'era', 'era': 'post_rift'},
]

# --- Hand-placed anchors ----------------------------------------------------
# Approximate positions read off the widely reproduced Games Workshop galaxy
# maps and the relative placements described in the lore. Each carries a
# short note that the inspector shows next to the coordinates.

SECTOR_ANCHORS = {
    'solar': (-6.0, -10.0, 1.2, 'Holds the Sol System at the centre of Segmentum Solar.'),
    'armageddon': (-8.0, -3.5, 1.5, 'North-west of Terra, towards the Eye of Terror, inside Segmentum Solar.'),
    'fenris': (-11.0, -5.0, 1.4, 'North-western edge of Segmentum Solar, near the Eye of Terror.'),
    'cadian': (-20.0, 12.5, 1.6, 'Guards the Cadian Gate at the Terra-facing edge of the Eye of Terror.'),
    'agripinaa': (-17.0, 11.0, 1.5, 'Neighbours the Cadian Gate, near the Eye of Terror.'),
    'gothic': (-14.0, 24.0, 2.5, 'Segmentum Obscurus, north of the Eye of Terror.'),
    'calixis': (-8.0, 40.0, 2.6, 'Segmentum Obscurus, beside the Koronus Expanse near the Halo Stars.'),
    'scarus': (-15.0, 35.0, 2.2, 'Segmentum Obscurus, neighbouring the Calixis Sector.'),
    'askellon': (-21.0, 29.0, 2.0, 'Segmentum Obscurus.'),
    'medusan': (-28.0, 31.0, 2.0, 'Segmentum Obscurus, towards the north-western rim.'),
    'nachmund': (-8.0, 3.5, 1.5, 'At the Nachmund Gauntlet, one of the few stable passages across the Great Rift.'),
    'abiaus': (-12.0, 18.0, 1.6, 'Segmentum Obscurus.'),
    'stygius': (8.0, 14.0, 2.2, 'Near the Obscurus/Ultima border.'),
    'ultima': (34.0, -18.0, 2.4, 'Ultramar, in the far east of Ultima Segmentum near the Eastern Fringe.'),
    'badab': (2.0, -5.5, 1.4, 'Ultima Segmentum, bordering the Maelstrom.'),
    'charadon': (27.0, -11.0, 2.0, 'Ultima Segmentum, north-west of Ultramar.'),
    'red-scar': (24.0, 4.0, 2.0, 'Ultima Segmentum, north of the Great Rift (Imperium Nihilus).'),
    'vidar': (38.0, -28.0, 2.0, 'Ultima Segmentum, south of Ultramar on the Eastern Fringe.'),
    'jericho': (45.0, 9.0, 3.0, 'The Jericho Reach, beyond the Eastern Fringe.'),
    'octarius': (39.0, -8.0, 2.2, 'Ultima Segmentum, Eastern Fringe, north of Ultramar.'),
    'prospero': (18.0, 14.0, 2.0, 'Ultima Segmentum.'),
    'nostramo': (36.0, 22.0, 2.0, 'Far north-east of Ultima Segmentum.'),
    'yasan': (22.0, -24.0, 2.0, 'Ultima Segmentum.'),
    'loki': (14.0, -15.0, 2.0, 'Ultima Segmentum.'),
    'aquitaine': (12.0, -24.0, 2.0, 'Ultima Segmentum.'),
    'uhulis': (-2.0, -36.0, 2.0, 'Segmentum Tempestus.'),
    'reductus': (6.0, -40.0, 2.0, 'Southern Segmentum Tempestus.'),
    'barbarus': (-20.0, -34.0, 2.0, 'Segmentum Tempestus.'),
    'macharian': (-34.0, -4.0, 2.5, 'Segmentum Pacificus, site of the Macharian Crusade.'),
    'macharius-alpha': (-31.0, -8.0, 1.8, 'Segmentum Pacificus.'),
    'sabbat-worlds': (-38.0, 4.0, 3.0, 'Segmentum Pacificus, towards the Obscurus border.'),
    'ullanor': (4.0, 1.0, 1.8, 'Towards the galactic core.'),
}

# (x, y, note). Where a world shares a system with others, anchor the
# system instead (SYSTEM_ANCHORS).
WORLD_ANCHORS = {
    'cthonia': (-5.5, -9.3, 'Close to Terra in Segmentum Solar.'),
    'gathalamor': (-3.5, -6.5, 'Segmentum Solar.'),
    'ryza': (-1.6, -13.2, 'Segmentum Solar.'),
    'necromunda': (-9.6, -14.6, 'Segmentum Solar, a short distance from Terra.'),
    'vostroya': (2.0, 12.0, 'Segmentum Obscurus.'),
    'caliban': (-25.0, 22.0, 'Segmentum Obscurus, north of the Eye of Terror. Destroyed; position is of the former world.'),
    'the-rock': (-24.4, 21.4, 'Mobile; drawn beside the remains of Caliban.'),
    'olympia': (-13.0, -15.0, 'Placed at the western edge of Segmentum Solar.'),
    'inwit': (12.0, 30.0, 'Placed in the far north of Ultima Segmentum.'),
    'nostramo': (36.5, 22.4, 'Placed in the Nostramo sector. Destroyed before the Horus Heresy.'),
    'nuceria': (-18.0, -18.0, 'Placed between Pacificus and Tempestus.'),
    'calth': (35.6, -16.4, 'One of the Five Hundred Worlds of Ultramar.'),
    'iax': (32.4, -19.6, 'One of the Five Hundred Worlds of Ultramar.'),
    'sotha': (38.8, -21.2, 'At the eastern edge of Ultramar.'),
    'prandium': (33.0, -16.6, 'One of the Five Hundred Worlds of Ultramar.'),
    'colchis': (-40.0, -14.0, 'Segmentum Pacificus. Destroyed.'),
    'nocturne': (16.0, -30.0, 'Ultima Segmentum.'),
    'kiavahr': (30.0, 14.0, 'Ultima Segmentum.'),
    'tallarn': (-16.0, -28.0, 'Segmentum Tempestus.'),
    'catachan': (-10.0, -42.0, 'Southern Segmentum Tempestus.'),
    'valhalla': (-26.0, -22.0, 'Placed near the Pacificus/Tempestus border.'),
    'tanith': (-37.2, 5.0, 'One of the Sabbat Worlds. Destroyed.'),
    't-au': (44.0, -14.0, "Heart of the T'au Empire, across the Damocles Gulf from Ultramar."),
    'vior-la': (45.6, -11.8, "T'au sept world near T'au."),
    'sa-cea': (46.0, -15.8, "T'au sept world near T'au."),
    'bork-an': (42.6, -11.6, "T'au sept world near T'au."),
    'dal-yth': (41.6, -13.6, "T'au sept world, on the Damocles Gulf side."),
    'au-taal': (43.6, -16.8, "T'au sept world near T'au."),
    'pech': (47.2, -10.0, "Kroot homeworld, inside the T'au sphere."),
    'vespid': (46.6, -17.8, "Vespid homeworld, inside the T'au sphere."),
    'agrellan-mu-gulath-bay': (40.0, -12.2, 'At the Damocles Gulf frontier.'),
    'solemnace': (37.0, -31.0, 'Necron-held region of the Eastern Fringe.'),
    'thanatos': (30.0, -38.0, 'Placed in the south-eastern rim.'),
    'serenade': (24.0, -34.0, 'Placed in the south-eastern rim.'),
    'drazak': (44.0, -30.0, 'Placed in the south-eastern rim.'),
    'charadon': (27.4, -10.6, 'Capital of the Charadon Ork empire.'),
    'angelis-gorkamorka': (20.0, -36.0, 'Placed in southern Ultima Segmentum.'),
    'sicarus': (-25.2, 17.4, 'Inside the Eye of Terror.'),
    'medrengard': (-22.6, 14.6, 'Inside the Eye of Terror.'),
    'plague-planet': (-25.8, 14.8, 'Inside the Eye of Terror.'),
    'eidolon': (-23.0, 17.6, 'Inside the Eye of Terror; former Aeldari world.'),
    'aktosha': (-24.6, 13.8, 'Inside the Eye of Terror; former Aeldari world.'),
    'sortiarius': (-23.4, 15.6, 'Inside the Eye of Terror in M41. Moved near Prospero after the Great Rift.'),
    'valedor': (28.0, -30.0, 'Ultima Segmentum. Destroyed.'),
    'commorragh': (1.4, 1.6, 'In the Webway, outside real space. The marker is symbolic only.'),
    'black-library': (-1.4, 1.2, 'In the Webway, outside real space. The marker is symbolic only.'),
    'ulthw': (-28.5, 12.0, 'Drifts at the edge of the Eye of Terror.'),
    'altansar': (-26.5, 19.0, 'Emerged from the Eye of Terror.'),
    'biel-tan': (-38.0, -22.0, 'Mobile craftworld; placed in the western rim.'),
    'iyanden': (40.0, 18.0, 'Mobile craftworld; placed in the eastern rim.'),
    'alaitoc': (-44.0, 18.0, 'Mobile craftworld; placed in the western rim.'),
    'saim-hann': (-20.0, 42.0, 'Mobile craftworld; placed in the northern rim.'),
    'lugganath': (30.0, -40.0, 'Mobile craftworld; placed in the south-eastern rim.'),
    'hydraphur': (-28.0, -12.0, 'Fortress world of Segmentum Pacificus.'),
    'cypra-mundi': (-4.0, 20.0, 'Fortress world of Segmentum Obscurus.'),
    'kar-duniash': (16.0, -6.0, 'Fortress world of Ultima Segmentum.'),
    'bakka': (-8.0, -32.0, 'Fortress world of Segmentum Tempestus.'),
    'gryphonne-iv': (-22.0, -30.0, 'Segmentum Tempestus, in the path of Hive Fleet Leviathan. Destroyed.'),
    'ophelia-vii': (-8.0, -20.0, 'Placed near the Solar/Tempestus border.'),
    'san-leor': (-11.0, -23.0, 'Placed near the Solar/Tempestus border.'),
}

SYSTEM_ANCHORS = {
    'solar-sol': (-6.0, -10.0, 'Sol, the origin of humanity and seat of the Imperium.'),
    'ultima-macragge': (34.0, -18.0, 'Macragge, capital of Ultramar.'),
    'cadian-cadian': (-20.0, 12.4, 'The Cadian Gate. Cadia was destroyed at the end of M41.'),
    'red-scar-baal': (24.0, 4.0, 'Baal, north of the Great Rift.'),
    'badab-badab': (2.0, -5.6, 'Badab, beside the Maelstrom.'),
    'armageddon-armageddon': (-8.0, -3.5, None),
    'fenris-fenris': (-11.0, -5.0, None),
    'nachmund-vigilus': (-7.4, 3.0, 'Vigilus guards the Nachmund Gauntlet.'),
    'prospero-prospero': (18.0, 14.0, None),
}

# Moons and their parent bodies, for the system view only.
MOON_PARENTS = {
    'luna': 'terra', 'phobos': 'mars', 'deimos': 'mars', 'titan': 'saturn',
    'ganymede': 'jupiter', 'baal-primus': 'baal', 'baal-secundus': 'baal',
    'prometheus': 'nocturne', 'deliverance': 'kiavahr',
}

# Bodies that share a system without a recorded system id.
SHARED_SYSTEMS = {'prometheus': 'nocturne', 'deliverance': 'kiavahr'}

SOL_ORDER = ['mercury', 'venus', 'terra', 'mars', 'ceres', 'jupiter', 'saturn',
             'uranus', 'neptune', 'pluto']

# Place names in a record's notes that pin it near a known place.
HINTS = [
    ('ultramar', ('sector', 'ultima')),
    ('sabbat', ('sector', 'sabbat-worlds')),
    ('octarius', ('sector', 'octarius')),
    ('damocles', ('point', 40.5, -14.0, 2.5, 'Damocles Gulf')),
    ('eye of terror', ('point', -24.0, 16.0, 6.0, 'Eye of Terror')),
    ('maelstrom', ('point', 0.0, -4.0, 2.5, 'Maelstrom')),
    ('koronus', ('point', -2.0, 43.0, 3.0, 'Koronus Expanse')),
    ('malfian', ('sector', 'calixis')),
    ('drusus', ('sector', 'calixis')),
    ('hazeroth', ('sector', 'calixis')),
    ('markayn', ('sector', 'calixis')),
    ('josian', ('sector', 'calixis')),
    ('periphery', ('sector', 'calixis')),
    ('spinward', ('sector', 'calixis')),
    ('adrantis', ('sector', 'calixis')),
    ('golgenna', ('sector', 'calixis')),
    ('calixis', ('sector', 'calixis')),
    ('helican', ('sector', 'scarus')),
    ('jericho', ('sector', 'jericho')),
    ('deathwatch', ('sector', 'jericho')),
    ('armageddon', ('sector', 'armageddon')),
    ('cadia', ('sector', 'cadian')),
    ('baal', ('sector', 'red-scar')),
    ('fenris', ('sector', 'fenris')),
    ('gothic', ('sector', 'gothic')),
    ('sautekh', ('sector', 'vidar')),
    ('leviathan', ('point', -20.0, -36.0, 7.0, 'path of Hive Fleet Leviathan')),
    ('behemoth', ('point', 40.0, -24.0, 4.0, 'path of Hive Fleet Behemoth')),
    ('kraken', ('point', 46.0, -4.0, 5.0, 'path of Hive Fleet Kraken')),
    ("t'au empire", ('point', 44.0, -14.0, 4.0, "T'au Empire")),
    ('damnos', ('sector', 'vidar')),
]

# Regions a faction is known to hold, used only when nothing else applies.
FACTION_REGIONS = {
    'orks': [
        (27.0, -11.0, 5.0, 'the Charadon Ork empire'),
        (39.0, -8.0, 4.0, 'the Octarius Ork empire'),
        (4.0, 1.0, 4.0, 'the Ullanor region'),
        (-8.0, -3.0, 3.0, 'the Armageddon region'),
        (18.0, -36.0, 6.0, 'the southern Ultima frontier'),
        (40.0, 24.0, 6.0, 'the north-eastern rim'),
    ],
    'tau': [(44.0, -14.0, 4.5, "the T'au Empire")],
    'chaos': [
        (-24.0, 16.0, 9.0, 'the Eye of Terror'),
        (-24.0, 16.0, 9.0, 'the Eye of Terror'),
        (-24.0, 16.0, 9.0, 'the Eye of Terror'),
        (0.0, -4.0, 4.0, 'the Maelstrom'),
    ],
}


# --- Geometry helpers -------------------------------------------------------

def rng_for(key):
    digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
    return random.Random(int(digest[:16], 16))


def bearing_from_terra(x, y):
    return math.degrees(math.atan2(y - TERRA[1], x - TERRA[0]))


def segmentum_of(x, y):
    if math.hypot(x - TERRA[0], y - TERRA[1]) <= SOLAR_RADIUS:
        return 'Solar'
    angle = bearing_from_terra(x, y)
    for name, (start, end) in WEDGES.items():
        for a in (angle, angle - 360, angle + 360):
            if start <= a < end:
                return name
    return 'Ultima'


def rift_y_at(x):
    points = GREAT_RIFT
    if x <= points[0][0]:
        return None
    if x >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return None


def rift_side_of(x, y):
    ry = rift_y_at(x)
    if ry is None:
        return 'Sanctus'
    return 'Nihilus' if y > ry else 'Sanctus'


def in_eye(x, y, margin=0.0):
    return math.hypot(x - EYE_OF_TERROR['x'], y - EYE_OF_TERROR['y']) < EYE_OF_TERROR['r'] + margin


def in_galaxy(x, y, inner=4.0, outer=GALAXY_RADIUS - 2.0):
    r = math.hypot(x, y)
    return inner <= r <= outer


def scatter(rng, cx, cy, radius):
    # Uniform within a disc.
    r = radius * math.sqrt(rng.random())
    a = rng.random() * math.tau
    return cx + r * math.cos(a), cy + r * math.sin(a)


def random_in_segmentum(rng, segmentum, avoid_eye=True):
    for _ in range(4000):
        if segmentum == 'Solar':
            x, y = scatter(rng, TERRA[0], TERRA[1], SOLAR_RADIUS - 0.6)
            if math.hypot(x - TERRA[0], y - TERRA[1]) < 1.6:
                continue
        else:
            r = GALAXY_RADIUS * math.sqrt(rng.uniform(0.02, 0.92))
            a = rng.random() * math.tau
            x, y = r * math.cos(a), r * math.sin(a)
        if not in_galaxy(x, y, inner=3.0):
            continue
        if segmentum_of(x, y) != segmentum:
            continue
        if avoid_eye and in_eye(x, y, 1.0):
            continue
        return x, y
    raise RuntimeError(f'could not sample {segmentum}')


def random_imperial(rng):
    for _ in range(4000):
        r = GALAXY_RADIUS * math.sqrt(rng.uniform(0.03, 0.9))
        a = rng.random() * math.tau
        x, y = r * math.cos(a), r * math.sin(a)
        if in_eye(x, y, 1.5):
            continue
        # Keep clear of the T'au sphere unless the record says otherwise.
        if math.hypot(x - 44.0, y - 14.0 * -1) < 5.0:
            continue
        return x, y
    raise RuntimeError('could not sample')


def random_rim(rng, inner=38.0, outer=GALAXY_RADIUS - 1.0):
    r = rng.uniform(inner, outer)
    a = rng.random() * math.tau
    return r * math.cos(a), r * math.sin(a)


# --- Classification ---------------------------------------------------------

def faction_of(loc):
    wt = (loc.get('world_type') or '').lower()
    aff = (loc.get('affiliation') or '').lower()
    text = f'{wt} | {aff}'
    kind = loc.get('location_kind')
    # The first-listed allegiance wins: "Imperium; contested by Orks and Chaos"
    # is an Imperial world.
    if aff.startswith('imperium'):
        return 'imperium'
    if kind == 'webway_city' or 'drukhari' in text or 'commorragh' in text:
        return 'drukhari'
    if 'crone' in wt or 'daemon' in text or 'chaos' in text or 'dark mechanicum' in text \
            or 'death guard' in text or 'sorcerer' in text:
        return 'chaos'
    if "t'au" in text or 'kroot' in text or 'vespid' in text:
        return 'tau'
    if 'necron' in text or 'tomb' in wt:
        return 'necrons'
    if kind == 'craftworld' or 'aeldari' in text or 'maiden' in wt or 'exodite' in wt:
        return 'aeldari'
    if 'tyranid' in text:
        return 'tyranids'
    if 'former ork' in text:
        return 'imperium' if 'imperium' in aff else 'contested'
    if 'ork' in text.replace('york', ''):
        return 'orks'
    if 'mechanicus' in aff or 'forge' in wt or 'knight' in text:
        return 'mechanicus' if 'knight' not in text else 'imperium'
    if 'imperium' in aff or 'imperial' in text or 'astartes' in text:
        return 'imperium'
    imperial_types = ['hive', 'agri', 'shrine', 'fortress', 'civilised', 'feudal', 'feral',
                      'frontier', 'war world', 'mining', 'industrial', 'penal', 'cardinal',
                      'paradise', 'pleasure', 'garden', 'sentinel', 'naval', 'research']
    if any(t in wt for t in imperial_types):
        return 'imperium'
    return 'unknown'


BIOME_RULES = [
    ('webway', 'webway'), ('craftworld', 'craftworld'), ('station', 'station'),
    ('naval base', 'station'), ('mobile', 'station'), ('repository', 'station'),
    ('daemon', 'daemon'), ('crone', 'daemon'), ('plague', 'daemon'), ('sorcerer', 'daemon'),
    ('tomb', 'tomb'), ('gas giant', 'gas'), ('molten', 'lava'), ('volcanic', 'lava'),
    ('irradiated', 'dead'), ('forge', 'forge'), ('hive', 'hive'), ('throne', 'hive'),
    ('ice', 'ice'), ('frozen', 'ice'), ('desert', 'desert'), ('ocean', 'ocean'),
    ('water', 'ocean'), ('jungle', 'jungle'), ('death', 'jungle'), ('swamp', 'jungle'),
    ('forest', 'jungle'), ('agri', 'agri'), ('garden', 'agri'), ('maiden', 'maiden'),
    ('ork', 'ork'), ('dead', 'dead'), ('wreck', 'dead'), ('destroyed', 'dead'),
    ('mining', 'mining'), ('asteroid', 'mining'), ('industrial', 'mining'),
    ('fortress', 'fortress'), ('war', 'fortress'), ('siege', 'fortress'), ('sentinel', 'fortress'),
    ('shrine', 'shrine'), ('cardinal', 'shrine'), ('feral', 'feral'), ('feudal', 'feral'),
    ('knight', 'feral'), ('civilised', 'temperate'), ('pleasure', 'temperate'),
    ('astartes', 'temperate'), ('frontier', 'temperate'), ('colon', 'temperate'),
    ('sept', 'temperate'), ('homeworld', 'temperate'), ('moon', 'dead'),
    ('outer system', 'ice'), ('xenos', 'alien'), ('quarantin', 'dead'), ('forbidden', 'dead'),
]


def biome_of(loc):
    wt = (loc.get('world_type') or '').lower()
    kind = loc.get('location_kind')
    if kind == 'craftworld':
        return 'craftworld'
    if kind == 'gas_giant':
        return 'gas'
    if kind == 'webway_city':
        return 'webway'
    if kind in ('space_station', 'artificial_habitat'):
        return 'station'
    for needle, biome in BIOME_RULES:
        if needle in wt:
            return biome
    return 'unknown'


def prominence_of(loc):
    if loc.get('factsheet_completeness') == 'curated_partial':
        return 3
    note = loc.get('notable') or ''
    generic = note.startswith(('Named in', 'Recorded in sector index', 'Attested named',
                               'Indexed'))
    return 1 if generic else 2


# --- Build ------------------------------------------------------------------

def main():
    db = json.loads(SOURCE.read_text(encoding='utf-8'))
    locations = db['locations']
    by_id = {loc['id']: loc for loc in locations}
    sectors = {s['id']: s for s in db['sectors']}
    subsectors = {s['id']: s for s in db['subsectors']}

    # Sectors ----------------------------------------------------------------
    sector_out = []
    sector_pos = {}
    member_segmenta = {}
    for loc in locations:
        if loc.get('sector_id') and loc.get('segmentum'):
            member_segmenta.setdefault(loc['sector_id'], []).append(loc['segmentum'])
    for sector in db['sectors']:
        sid = sector['id']
        rng = rng_for(f'sector:{sid}')
        seg = sector.get('segmentum')
        inferred_from_worlds = False
        if not seg and member_segmenta.get(sid):
            from collections import Counter
            seg = Counter(member_segmenta[sid]).most_common(1)[0][0]
            inferred_from_worlds = True
        if sid in SECTOR_ANCHORS:
            x, y, radius, note = SECTOR_ANCHORS[sid]
            method, confidence = 'anchor', 'approximate'
        elif seg:
            x, y = random_in_segmentum(rng, seg)
            radius = 2.0
            note = (f'No published position found. Placed at random inside Segmentum {seg}, '
                    + ('the segmentum recorded for its worlds.' if inferred_from_worlds
                       else 'where the sector index lists it.'))
            method, confidence = 'segmentum', 'guess'
        else:
            x, y = random_imperial(rng)
            radius = 2.0
            note = 'Neither position nor segmentum is recorded. Placed at random in Imperial space.'
            method, confidence = 'random', 'guess'
        sector_pos[sid] = (x, y, radius)
        out = dict(sector)
        out.update({
            'x': round(x, 3), 'y': round(y, 3), 'radius': radius,
            'placement': {'method': method, 'confidence': confidence, 'note': note},
            'segmentum_estimated': None if sector.get('segmentum') else segmentum_of(x, y),
        })
        sector_out.append(out)

    # Subsectors: an offset inside their parent sector.
    subsector_pos = {}
    for sub in db['subsectors']:
        parent = sector_pos.get(sub.get('sector_id'))
        if not parent:
            continue
        rng = rng_for(f'subsector:{sub["id"]}')
        if sub['id'] == f'{sub["sector_id"]}-{sub["sector_id"]}' or sub['id'] == 'solar-sol':
            x, y = parent[0], parent[1]
        else:
            x, y = scatter(rng, parent[0], parent[1], parent[2] * 0.7)
        subsector_pos[sub['id']] = (x, y, parent[2] * 0.4)

    # Systems ----------------------------------------------------------------
    system_pos = {}
    system_meta = {}
    for system in db['systems']:
        sid = system['id']
        rng = rng_for(f'system:{sid}')
        if sid in SYSTEM_ANCHORS:
            x, y, note = SYSTEM_ANCHORS[sid]
            sector = sectors.get(system['sector_id'])
            note = note or f'Placed at the centre of the {sector["name"] if sector else "?"} sector.'
            method, confidence = 'anchor', 'approximate'
        elif system.get('subsector_id') in subsector_pos:
            cx, cy, r = subsector_pos[system['subsector_id']]
            x, y = scatter(rng, cx, cy, r)
            sub = subsectors[system['subsector_id']]
            note = f'Placed inside the {sub["name"]} subsector of its sector; exact position unknown.'
            method, confidence = 'subsector', 'approximate'
        elif system.get('sector_id') in sector_pos:
            cx, cy, r = sector_pos[system['sector_id']]
            x, y = scatter(rng, cx, cy, r * 0.85)
            note = f'Placed inside the {sectors[system["sector_id"]]["name"]} sector; exact position unknown.'
            method, confidence = 'sector', 'approximate'
        else:
            x, y = random_imperial(rng)
            note = 'No sector recorded; placed at random.'
            method, confidence = 'random', 'guess'
        system_pos[sid] = (x, y)
        system_meta[sid] = {'method': method, 'confidence': confidence, 'note': note}

    # Worlds -----------------------------------------------------------------
    placements = {}

    def describe_sector(sid):
        sector = sectors.get(sid)
        return sector['name'] if sector else sid

    for loc in locations:
        lid = loc['id']
        rng = rng_for(f'world:{lid}')
        seg = loc.get('segmentum')
        sector_id = loc.get('sector_id')
        text = ' '.join(str(v) for v in [
            loc.get('notable'), loc.get('name'),
            *[n.get('note') for n in loc.get('source_notes') or []],
        ]).lower()
        faction = faction_of(loc)

        placement = None
        if lid in WORLD_ANCHORS:
            x, y, note = WORLD_ANCHORS[lid]
            placement = (x, y, 'anchor', 'approximate', note)
        elif loc.get('system_id') in system_pos:
            x, y = system_pos[loc['system_id']]
            meta = system_meta[loc['system_id']]
            placement = (x, y, 'system', meta['confidence'],
                         f'Shares its star system. {meta["note"]}')
        elif lid in SHARED_SYSTEMS:
            continue  # resolved after its host body is placed
        elif loc.get('subsector_id') in subsector_pos:
            cx, cy, r = subsector_pos[loc['subsector_id']]
            x, y = scatter(rng, cx, cy, r)
            sub = subsectors[loc['subsector_id']]
            placement = (x, y, 'subsector', 'approximate',
                         f'Recorded in the {sub["name"]} subsector of the {describe_sector(sub["sector_id"])} sector. '
                         'Placed at random inside that subsector.')
        elif sector_id in sector_pos:
            cx, cy, r = sector_pos[sector_id]
            for _ in range(60):
                x, y = scatter(rng, cx, cy, r)
                if not seg or segmentum_of(x, y) == seg:
                    break
            placement = (x, y, 'sector', 'approximate',
                         f'Recorded in the {describe_sector(sector_id)} sector. Placed at random inside that sector\'s footprint.')
        else:
            for needle, target in HINTS:
                if needle not in text:
                    continue
                if target[0] == 'sector':
                    hint_xy = sector_pos.get(target[1], (0, 0))[:2]
                else:
                    hint_xy = target[1:3]
                if seg and segmentum_of(*hint_xy) != seg:
                    continue  # the recorded segmentum wins over a place-name hint
                if target[0] == 'sector' and target[1] in sector_pos:
                    cx, cy, r = sector_pos[target[1]]
                    x, y = scatter(rng, cx, cy, r * 1.1)
                    placement = (x, y, 'hint', 'guess',
                                 f'Its notes mention "{needle}", so it is drawn in the {describe_sector(target[1])} sector.')
                elif target[0] == 'point':
                    _, cx, cy, r, label = target
                    x, y = scatter(rng, cx, cy, r)
                    placement = (x, y, 'hint', 'guess',
                                 f'Its notes mention "{needle}", so it is drawn near {label}.')
                if placement:
                    break

        if placement is None and seg:
            avoid = faction != 'chaos'
            x, y = random_in_segmentum(rng, seg, avoid_eye=avoid)
            placement = (x, y, 'segmentum', 'guess',
                         f'Only its segmentum ({seg}) is recorded. Placed at random inside Segmentum {seg}.')

        if placement is None:
            if loc.get('location_kind') == 'craftworld':
                x, y = random_rim(rng)
                placement = (x, y, 'faction', 'guess',
                             'Craftworlds drift between the stars and most positions are unpublished. '
                             'Placed at random along the galactic rim, where the craftworlds are generally described.')
            elif faction in FACTION_REGIONS:
                cx, cy, r, label = rng.choice(FACTION_REGIONS[faction])
                for _ in range(200):
                    x, y = scatter(rng, cx, cy, r)
                    if faction == 'chaos' or not in_eye(x, y, 0.5):
                        break
                placement = (x, y, 'faction', 'guess',
                             f'No location is recorded. As a {faction_label(faction)} world it is drawn in {label}.')
            elif faction == 'necrons':
                for _ in range(500):
                    x, y = random_rim(rng, inner=26.0)
                    if not in_eye(x, y, 2.0):
                        break
                placement = (x, y, 'faction', 'guess',
                             'No location is recorded. Placed in the outer galaxy, where most tomb worlds '
                             'are described as stirring.')
            else:
                x, y = random_imperial(rng)
                placement = (x, y, 'random', 'guess',
                             'No sector, segmentum or regional clue is recorded. Placed at random in Imperial space '
                             'so that it can be browsed; treat the position as meaningless.')
        placements[lid] = placement

    for lid, host in SHARED_SYSTEMS.items():
        hx, hy = placements[host][0], placements[host][1]
        placements[lid] = (hx, hy, 'system', 'approximate',
                           f'Orbits in the same system as {by_id[host]["name"]}.')

    # Worlds named "<Base> <numeral>" or "<Base> Secundus" etc. with no
    # recorded system are assumed to share a system with the other worlds of
    # the same base name.
    name_groups = {}
    for loc in locations:
        if loc.get('system_id') or loc['id'] in SHARED_SYSTEMS:
            continue
        if loc.get('location_kind') in ('craftworld', 'webway_city', 'space_station'):
            continue
        base, slot = split_designation(loc['name'])
        name_groups.setdefault(base.lower(), []).append(loc['id'])
    for base, members in name_groups.items():
        if len(members) < 2:
            continue
        if not any(split_designation(by_id[m]['name'])[1] or by_id[m]['name'] != split_designation(by_id[m]['name'])[0]
                   for m in members):
            continue  # identical names (same-name conflicts) are different worlds
        names = {by_id[m]['name'] for m in members}
        if len(names) < len(members):
            continue
        rank = {'anchor': 0, 'system': 1, 'subsector': 2, 'sector': 3, 'hint': 4,
                'segmentum': 5, 'faction': 6, 'random': 7}
        host = min(members, key=lambda m: (rank[placements[m][2]], -prominence_of(by_id[m]), m))
        hx, hy, hmethod, hconf, hnote = placements[host]
        host_seg = by_id[host].get('segmentum')
        for m in members:
            if m == host:
                continue
            seg_m = by_id[m].get('segmentum')
            if seg_m and host_seg and seg_m != host_seg:
                continue  # recorded in different segmenta: not the same system
            SHARED_SYSTEMS[m] = host
            placements[m] = (hx, hy, 'system', hconf,
                             f'Assumed to share a system with {by_id[host]["name"]} because of the shared name. '
                             f'{hnote}')

    # Spread out scattered points so markers don't sit on top of each other.
    relax(placements, by_id)

    # Group worlds into systems ---------------------------------------------
    systems_out = {}
    for system in db['systems']:
        x, y = system_pos[system['id']]
        systems_out[system['id']] = {
            'id': system['id'], 'name': system['name'].replace(' System', ''),
            'sector_id': system.get('sector_id'), 'subsector_id': system.get('subsector_id'),
            'source_url': system.get('source_url'), 'synthetic': False,
            'x': x, 'y': y, 'worlds': [], 'placement': system_meta[system['id']],
        }

    worlds_out = []
    for loc in locations:
        lid = loc['id']
        x, y, method, confidence, note = placements[lid]
        sys_id = loc.get('system_id')
        if lid in SHARED_SYSTEMS:
            sys_id = by_id[SHARED_SYSTEMS[lid]].get('system_id') or f'sys-{SHARED_SYSTEMS[lid]}'
        if not sys_id or sys_id not in systems_out and not sys_id.startswith('sys-'):
            sys_id = f'sys-{lid}'
        if sys_id not in systems_out:
            host_id = SHARED_SYSTEMS.get(lid, lid)
            systems_out[sys_id] = {
                'id': sys_id, 'name': split_designation(by_id[host_id]['name'])[0],
                'sector_id': loc.get('sector_id'),
                'subsector_id': loc.get('subsector_id'), 'source_url': None, 'synthetic': True,
                'x': x, 'y': y, 'worlds': [],
                'placement': {'method': method, 'confidence': confidence, 'note': note},
            }
        systems_out[sys_id]['worlds'].append(lid)

        out = {k: v for k, v in loc.items() if v not in (None, '', [], {})}
        z = rng_for(f'z:{lid}').gauss(0, 0.22) * max(0.15, 1 - math.hypot(x, y) / 60)
        out.update({
            'x': round(x, 3), 'y': round(y, 3), 'z': round(z, 3),
            'system': sys_id,
            'faction': faction_of(loc),
            'biome': biome_of(loc),
            'prominence': prominence_of(loc),
            'placement': {'method': method, 'confidence': confidence, 'note': note},
            'segmentum_estimated': segmentum_of(x, y),
            'rift_side_estimated': rift_side_of(x, y),
            'parent': MOON_PARENTS.get(lid),
        })
        worlds_out.append(out)

    # Order bodies inside each system and fill the smaller systems out with
    # generated, undocumented worlds. Sol keeps its real order and is not
    # padded.
    world_index = {w['id']: w for w in worlds_out}
    known_names = {loc['name'].lower() for loc in locations}
    generated = []
    for system in systems_out.values():
        if system['id'] == 'solar-sol':
            primary = 'terra'
        elif not system['worlds']:
            primary = None  # a named system with no documented bodies
        else:
            primary = max(system['worlds'], key=lambda w: (prominence_of(by_id[w]),
                                                           by_id[w]['location_kind'] == 'planet', w))
        system['primary'] = primary
        system['x'] = round(system['x'], 3)
        system['y'] = round(system['y'], 3)
        system['star'] = star_for(system['id'])
        generated.extend(lay_out_system(system, world_index, known_names))

    # Each body in a system draws at the system's point.
    for system in systems_out.values():
        primary = world_index[system['primary']]
        primary.setdefault('z', 0.0)
        for wid in system['worlds']:
            world = world_index.get(wid)
            if world is None:
                continue
            world['x'], world['y'] = system['x'], system['y']
            world['z'] = primary['z']
    for world in generated:
        system = systems_out[world['system']]
        primary = world_index[system['primary']]
        world.update({'x': system['x'], 'y': system['y'], 'z': primary.get('z', 0.0),
                      'segmentum_estimated': segmentum_of(system['x'], system['y']),
                      'rift_side_estimated': rift_side_of(system['x'], system['y'])})
    # The app supplies the shared placement note for generated worlds.
    worlds_out.extend({k: v for k, v in g.items() if v is not None and v is not False}
                      for g in generated)

    data = {
        'title': 'Galactic Atlas of the 41st Millennium',
        'research_date': db.get('research_date'),
        'accuracy_notice': db.get('accuracy_notice'),
        'scope': db.get('scope'),
        'frame': {
            'unit': 'kly',
            'galaxy_radius': GALAXY_RADIUS,
            'terra': {'x': TERRA[0], 'y': TERRA[1]},
            'solar_radius': SOLAR_RADIUS,
            'wedges': WEDGES,
            'note': ('Positions are best guesses. No official, consistently projected coordinates exist; '
                     'the frame follows the general layout of the published Games Workshop galaxy maps.'),
        },
        'features': {
            'eye_of_terror': EYE_OF_TERROR,
            'maelstrom': MAELSTROM,
            'great_rift': [{'x': x, 'y': y} for x, y in GREAT_RIFT],
            'regions': REGION_LABELS,
        },
        'eras': db.get('eras'),
        'segmenta': db.get('segmenta'),
        'sectors': sector_out,
        'subsectors': db['subsectors'],
        'systems': list(systems_out.values()),
        'worlds': worlds_out,
        'primarchs': db.get('primarchs'),
        'faction_homeworlds': db.get('faction_homeworlds'),
        'aliases': db.get('potential_duplicates_and_aliases'),
        'same_name_conflicts': db.get('same_name_different_planets'),
        'tau_septs': db.get('tau_sept_names_not_verified_planets'),
        'region_notes': db.get('region_notes'),
        'sources': db.get('sources'),
        'coverage': db.get('coverage'),
        'limitations': db.get('source_specific_limitations'),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    from collections import Counter
    methods = Counter(w['placement']['method'] for w in worlds_out if not w.get('generated'))
    print('Generated undocumented worlds:', sum(1 for w in worlds_out if w.get('generated')))
    print('Generated classes:', dict(Counter(w['world_type'] for w in worlds_out if w.get('generated'))))
    print(f'Wrote {OUTPUT.relative_to(ROOT)}: {len(worlds_out)} worlds, '
          f'{len(systems_out)} systems, {len(sector_out)} sectors')
    print('Placement methods:', dict(methods))


def faction_label(faction):
    return {
        'orks': 'Ork', 'tau': "T'au", 'chaos': 'Chaos-held', 'necrons': 'Necron',
    }.get(faction, faction)


STAR_PALETTE = [
    ('G-type (yellow)', [1.0, 0.92, 0.72]),
    ('K-type (orange)', [1.0, 0.76, 0.48]),
    ('M-type (red dwarf)', [1.0, 0.56, 0.38]),
    ('F-type (yellow-white)', [1.0, 0.97, 0.88]),
    ('A-type (white)', [0.9, 0.94, 1.0]),
]


def star_for(system_id):
    if system_id == 'solar-sol':
        return {'label': 'Sol (G-type)', 'color': [1.0, 0.93, 0.74], 'schematic': False}
    label, color = rng_for(f'star:{system_id}').choice(STAR_PALETTE)
    return {'label': label, 'color': color, 'schematic': True}


def relax(placements, by_id, min_sep=0.42, passes=30):
    """Push apart scattered (non-anchored, non-system) markers."""
    movable = {lid for lid, p in placements.items()
               if p[2] not in ('anchor', 'system') and lid not in SHARED_SYSTEMS.values()}
    ids = list(placements)
    pos = {lid: [placements[lid][0], placements[lid][1]] for lid in ids}
    # Bodies of one system share a point; collapse them for spacing purposes.
    for _ in range(passes):
        moved = False
        grid = {}
        for lid in ids:
            key = (int(pos[lid][0] // min_sep), int(pos[lid][1] // min_sep))
            grid.setdefault(key, []).append(lid)
        for lid in movable:
            px, py = pos[lid]
            gx, gy = int(px // min_sep), int(py // min_sep)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for other in grid.get((gx + dx, gy + dy), []):
                        if other == lid:
                            continue
                        ox, oy = pos[other]
                        d = math.hypot(px - ox, py - oy)
                        if d < min_sep:
                            if d < 1e-6:
                                angle = rng_for(f'{lid}:{other}').random() * math.tau
                                ux, uy = math.cos(angle), math.sin(angle)
                            else:
                                ux, uy = (px - ox) / d, (py - oy) / d
                            push = (min_sep - d) * 0.6
                            px += ux * push
                            py += uy * push
                            moved = True
            pos[lid] = [px, py]
        if not moved:
            break
    for lid in movable:
        x, y = pos[lid]
        old = placements[lid]
        # Never let spacing push a point across a recorded segmentum border.
        seg = by_id[lid].get('segmentum')
        if seg and segmentum_of(x, y) != seg:
            continue
        placements[lid] = (x, y, *old[2:])


# --- Undocumented worlds ----------------------------------------------------
# Generated bodies that fill out systems the corpus only names one or two
# worlds in. They are flagged `generated` everywhere and never drawn from, or
# presented as, published lore. The class mix follows the Imperial survey
# pattern: dead and uninhabitable worlds and gas giants vastly outnumber
# inhabited ones; feral, feudal, death, penal, shrine and agri worlds are
# common among the inhabited; hive and forge worlds are rare.

ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII',
         'XIII', 'XIV', 'XV', 'XVI']
ORDINALS = {'primus': 1, 'secundus': 2, 'tertius': 3, 'quartus': 4, 'quintus': 5}
SUFFIXES = ('prime', 'primaris', 'majoris', 'minoris')


def split_designation(name):
    """'Ophelia VII' -> ('Ophelia', 7); 'Zel Secundus' -> ('Zel', 2); 'Voss Prime' -> ('Voss', None)."""
    clean = name.split(' (')[0].strip()
    parts = clean.split(' ')
    if len(parts) > 1:
        last = parts[-1]
        if last in ROMAN[1:]:
            return ' '.join(parts[:-1]), ROMAN.index(last)
        if last.lower() in ORDINALS:
            return ' '.join(parts[:-1]), ORDINALS[last.lower()]
        if last.lower() in SUFFIXES:
            return ' '.join(parts[:-1]), None
    if clean.lower().endswith('-prime'):
        return clean[:-6], None
    return clean, None


GEN_CLASSES = {
    'scorched': {
        'label': 'Dead World', 'variant': 'scorched', 'code': 'δ', 'biome': 'lava',
        'surface': ['Sun-blasted bedrock and slag plains; dayside rock runs molten.',
                    'Cracked basalt and glassy impact melt under constant stellar glare.',
                    'Tidally locked: a molten dayside and a cooling, cratered terminator.'],
        'atmosphere': ['None.', 'Trace sodium and sulphur vapour.', 'Thin, scalding rock vapour.'],
        'notes': ['Logged as a navigational hazard and nothing more.',
                  'Survey records list it only by its orbital designation.',
                  'Too close to its star for anything but automated ore-skimmers.'],
    },
    'dead': {
        'label': 'Dead World', 'variant': 'barren', 'code': 'δ', 'biome': 'dead',
        'surface': ['Airless, cratered rock with no native life.',
                    'Grey regolith plains and ancient impact basins.',
                    'Bedrock scoured bare. Survey notes suggest the scarring is not natural.',
                    'Ash deserts and fused glass; the old cities are only outlines now.'],
        'atmosphere': ['None.', 'Trace carbon dioxide; unbreathable.', 'Thin and toxic.'],
        'notes': ['Generates no tithe; charted as a tactical asset only.',
                  'An abandoned Imperial survey beacon still broadcasts from orbit.',
                  'Exterminatus is recorded against this world in sealed Inquisitorial files.',
                  'A Tyranid hive fleet stripped its biosphere to the rock.',
                  'Records of what happened here were purged.'],
    },
    'ice': {
        'label': 'Dead World', 'variant': 'frozen', 'code': 'δ', 'biome': 'ice',
        'surface': ['Water and methane ice over a frozen rock core.',
                    'Nitrogen glaciers and a cracked ice crust.',
                    'Dark, frozen plains; the star is a bright point in its sky.'],
        'atmosphere': ['None.', 'Thin nitrogen and methane haze.', 'Frozen out onto the surface.'],
        'notes': ['Charted for navigation only.',
                  'A Navy listening post sits on one of its ice shelves.',
                  'Rogue-trader ice haulers occasionally mine its crust.'],
    },
    'gas': {
        'label': 'Gas Giant', 'variant': None, 'code': None, 'biome': 'gas',
        'surface': ['No solid surface; banded hydrogen-helium cloud decks.',
                    'Storm-wracked cloud bands over a deep, crushing atmosphere.',
                    'Pale, hazy cloud tops with few visible bands.'],
        'atmosphere': ['Hydrogen and helium with ammonia and methane clouds.',
                       'Hydrogen and helium; deep storm systems.'],
        'notes': ['Promethium gas-skimmers work its upper atmosphere.',
                  'Its moons shelter a minor Navy refuelling station.',
                  'Uninhabited; logged as a fuel source for passing ships.'],
    },
    'feral': {
        'label': 'Feral World', 'variant': None, 'code': None, 'biome': 'feral',
        'surface': ['Untamed continents of forest, steppe and mountain.',
                    'Grasslands and broken highlands scattered with ruins of an older age.',
                    'Archipelagos and river valleys home to scattered tribes.'],
        'atmosphere': ['Breathable.', 'Breathable; seasonal storms.'],
        'notes': ['Tribes fight with spear, axe and bow, unaware of the Imperium.',
                  'An Astartes chapter takes its strongest young warriors as recruits.',
                  'The Imperium watches it from orbit and does not intervene.'],
    },
    'feudal': {
        'label': 'Feudal World', 'variant': None, 'code': 'μ', 'biome': 'feral',
        'surface': ['Farmland, forests and walled towns ruled from stone keeps.',
                    'Rolling agricultural country divided between rival kingdoms.',
                    'Castle-crowned hills over fertile river plains.'],
        'atmosphere': ['Breathable.', 'Breathable; temperate.'],
        'notes': ['Knightly orders and feudal lords swear fealty to a distant "Sky Emperor".',
                  'Its disciplined warrior aristocracy is valued as a recruiting ground.',
                  'Tithes are paid in grain and in sons sent to the Astra Militarum.'],
    },
    'death': {
        'label': 'Death World', 'variant': None, 'code': 'δτ', 'biome': 'jungle',
        'surface': ['Predatory jungle in which almost every plant and animal is lethal.',
                    'Volcanic ice fields swept by killing storms.',
                    'Radiation-scorched desert where survivors live in deep caves.'],
        'atmosphere': ['Breathable but spore-laden.', 'Breathable; violent storms.',
                       'Breathable at depth; irradiated at the surface.'],
        'notes': ['Only the toughest survivors endure; the Guard recruits them.',
                  'A tiny survivalist population ekes out a living.',
                  'Imperial surveys have lost several teams to its wildlife.'],
    },
    'penal': {
        'label': 'Penal World', 'variant': None, 'code': None, 'biome': 'mining',
        'surface': ['Mine-riddled crust; sealed prison blocks cover whole continents.',
                    'Subterranean penal levels under a poisoned surface.',
                    'Bleak tundra ringed by orbital watch platforms.'],
        'atmosphere': ['Marginal; respirators required.', 'Breathable but heavily polluted.'],
        'notes': ['Managed remotely from orbit; gangs run the prison levels.',
                  'Convicts work its mines until they die.',
                  'A source of penal legion troops.'],
    },
    'shrine': {
        'label': 'Shrine World', 'variant': None, 'code': 'ε', 'biome': 'shrine',
        'surface': ['Cathedral-cities and endless pilgrim roads.',
                    'Planet-wide catacombs and martyrs\' cemeteries.',
                    'Basilicas and reliquaries cover the habitable continents.'],
        'atmosphere': ['Breathable; heavy with incense smoke.', 'Breathable.'],
        'notes': ['Holds the relics of a minor saint; pilgrims arrive by the shipload.',
                  'A cemetery world for the Imperial Creed\'s martyrs.',
                  'Governed by the Ecclesiarchy.'],
    },
    'agri': {
        'label': 'Agri World', 'variant': None, 'code': 'α', 'biome': 'agri',
        'surface': ['Machine-worked crop belts from pole to pole.',
                    'Grox ranges and grain plains under polluted, artificial skies.',
                    'Terraced hydroponic continents and fertiliser plants.'],
        'atmosphere': ['Breathable; agrochemical haze.', 'Breathable.'],
        'notes': ['Its harvests feed the hive worlds of the sub-sector.',
                  'Food tithe quotas are enforced by the Adeptus Arbites.',
                  'A small population of workers and servitors runs the harvests.'],
    },
    'civilised': {
        'label': 'Civilised World', 'variant': None, 'code': None, 'biome': 'temperate',
        'surface': ['Continents of cities, farmland and wilderness.',
                    'Temperate, settled world with scattered urban centres.',
                    'Coastal cities and inland manufactoria.'],
        'atmosphere': ['Breathable.', 'Breathable; mild industrial pollution.'],
        'notes': ['Self-sufficient; it pays its tithe and raises regiments.',
                  'Ruled by a hereditary Imperial governor.',
                  'Unremarkable by Imperial standards.'],
    },
    'mining': {
        'label': 'Mining World', 'variant': None, 'code': None, 'biome': 'mining',
        'surface': ['Strip-mined crust and open ore pits.',
                    'Mountain ranges hollowed out by deep mineshafts.',
                    'Asteroid-strewn rock surrounded by ore refineries.'],
        'atmosphere': ['Thin; respirators required.', 'Toxic; workers live in sealed habs.'],
        'notes': ['Its ores are shipped to the nearest forge world.',
                  'Mining guilds and indentured workers make up its population.',
                  'Kept in production by the Administratum\'s quotas.'],
    },
    'hive': {
        'label': 'Hive World', 'variant': None, 'code': 'η', 'biome': 'hive',
        'surface': ['Kilometres-high hive cities over poisoned ash wastes.',
                    'A handful of vast hive spires; little of the original surface remains.',
                    'Hive stacks linked by transit lines across polluted plains.'],
        'atmosphere': ['Heavily polluted; outside the hives, respirators required.',
                       'Toxic smog over the ash wastes.'],
        'notes': ['Holds most of the human population of the system.',
                  'Its underhives are lawless and its noble houses vicious.',
                  'Supplies huge levies to the Astra Militarum.'],
    },
    'forge': {
        'label': 'Forge World', 'variant': None, 'code': 'φ', 'biome': 'forge',
        'surface': ['Continent-spanning manufactoria and slag plains.',
                    'Smoke-choked forge complexes over a mined-out crust.',
                    'Factory-temples among lava-lit refineries.'],
        'atmosphere': ['Toxic with industrial effluent.', 'Barely breathable; heavy metals.'],
        'notes': ['A minor forge of the Adeptus Mechanicus, sworn to Mars.',
                  'Builds munitions and void-ship parts for the sector fleet.',
                  'Its Fabricator guards its secrets.'],
    },
}

ZONE_WEIGHTS = {
    'inner': {'scorched': 6, 'dead': 3, 'mining': 1, 'penal': 0.3, 'forge': 0.2},
    'middle': {'dead': 3, 'civilised': 2, 'agri': 1.2, 'feral': 1.1, 'feudal': 1.0,
               'death': 1.1, 'mining': 1.0, 'shrine': 0.6, 'penal': 0.6, 'hive': 0.35,
               'forge': 0.25},
    'outer': {'gas': 5, 'ice': 4, 'dead': 1.5, 'mining': 0.5, 'penal': 0.25},
}
XENOS_ALLOWED = {'scorched', 'dead', 'ice', 'gas', 'death'}
XENOS_FACTIONS = {'orks', 'necrons', 'chaos', 'tau', 'aeldari', 'drukhari', 'tyranids'}

POPULATION = {
    'scorched': (0, 0), 'dead': (0, 0), 'ice': (0, 0), 'gas': (0, 0),
    'feral': (2e5, 5e6), 'feudal': (1e6, 2e8), 'death': (1e5, 3e6), 'penal': (1e5, 5e7),
    'shrine': (1e6, 2e9), 'agri': (5e6, 5e8), 'civilised': (1e8, 1e10),
    'mining': (1e5, 1e7), 'hive': (5e10, 4e11), 'forge': (1e9, 5e10),
}
TITHE = {
    'scorched': 'Aptus Non', 'dead': 'Aptus Non', 'ice': 'Aptus Non', 'gas': 'Solutio Tertius',
    'feral': 'Solutio Tertius', 'feudal': 'Solutio Prima', 'death': 'Solutio Tertius',
    'penal': 'Decuma Tertius', 'shrine': 'Solutio Particular', 'agri': 'Exactis Prima',
    'civilised': 'Decuma Particular', 'mining': 'Exactis Particular', 'hive': 'Exactis Extremis',
    'forge': 'Adeptus Non',
}
TEMPERATURE = {'inner': (180, 460), 'middle': (-25, 42), 'outer': (-230, -130)}
DEATH_VARIANTS = [('jungle', 0), ('ice', 1), ('desert', 2)]


def weighted_choice(rng, weights):
    total = sum(weights.values())
    pick = rng.random() * total
    for key, weight in weights.items():
        pick -= weight
        if pick <= 0:
            return key
    return key


def format_population(n):
    if n <= 0:
        return 'None'
    for value, word in ((1e9, 'billion'), (1e6, 'million'), (1e3, 'thousand')):
        if n >= value:
            return f'~{n / value:.0f} {word}' if n / value >= 10 else f'~{n / value:.1f} {word}'
    return f'~{n:.0f}'


def preferred_fraction(biome):
    return {'lava': 0.05, 'gas': 0.75, 'ice': 0.9}.get(biome, 0.4)


def lay_out_system(system, world_index, known_names):
    """Assign orbit slots and return any generated worlds for this system."""
    docs = system['worlds']
    system['orbit_order'] = 'real' if system['id'] == 'solar-sol' else 'schematic'
    if system['id'] == 'solar-sol':
        order = {wid: i for i, wid in enumerate(SOL_ORDER)}
        for i, wid in enumerate(sorted((w for w in docs if not world_index[w].get('parent')),
                                       key=lambda w: order.get(w, 99))):
            world_index[wid]['slot'] = i + 1
        system['worlds'] = order_with_moons(docs, world_index)
        system['generated_count'] = 0
        return []

    bodies = [w for w in docs if not (world_index[w].get('parent') in docs)]
    biomes = {world_index[w]['biome'] for w in bodies}
    if biomes & {'craftworld', 'webway', 'station'} and len(bodies) == 1:
        world_index[bodies[0]]['slot'] = None
        system['generated_count'] = 0
        system['free_floating'] = True
        return []

    rng = rng_for(f'fill:{system["id"]}')
    n = int(weighted_choice(rng, {4: 1, 5: 2, 6: 3, 7: 3, 8: 3, 9: 2, 10: 1.5, 11: 1}))
    slots = {}
    numbered = []
    for wid in bodies:
        _, number = split_designation(world_index[wid]['name'])
        if number and number <= 16 and number not in slots:
            slots[number] = wid
            numbered.append(number)
    n = max(n, len(bodies) + 1, max(numbered, default=0) + rng.randint(0, 2))
    for wid in bodies:
        if wid in slots.values():
            continue
        target = round(preferred_fraction(world_index[wid]['biome']) * (n - 1)) + 1
        free = [i for i in range(1, n + 1) if i not in slots]
        best = min(free, key=lambda i: (abs(i - target), i))
        slots[best] = wid
    for slot, wid in slots.items():
        world_index[wid]['slot'] = slot

    primary = world_index[system['primary']] if system['primary'] else {'faction': 'imperium'}
    xenos = primary['faction'] in XENOS_FACTIONS
    base = system['name']
    generated = []
    for slot in range(1, n + 1):
        if slot in slots:
            continue
        frac = (slot - 1) / max(1, n - 1)
        zone = 'inner' if frac < 0.22 else 'outer' if frac > 0.62 else 'middle'
        weights = ZONE_WEIGHTS[zone]
        if xenos:
            weights = {k: v for k, v in weights.items() if k in XENOS_ALLOWED} or {'dead': 1}
            if zone == 'middle':
                weights = {'dead': 3, 'death': 1.5, 'scorched': 0.5}
        cls = weighted_choice(rng, weights)
        generated.append(make_generated_world(rng, system, slot, n, zone, cls, base,
                                              primary, xenos, known_names))
    for world in generated:
        world_index[world['id']] = world
    if not system['primary']:
        system['primary'] = max(generated, key=lambda g: (g['population'], g['id']))['id']
    system['worlds'] = order_with_moons(docs + [g['id'] for g in generated], world_index)
    system['generated_count'] = len(generated)
    return generated


def order_with_moons(ids, world_index):
    bodies = sorted((w for w in ids if not world_index[w].get('parent') or world_index[w]['parent'] not in ids),
                    key=lambda w: (world_index[w].get('slot') or 99, w))
    ordered = []
    for body in bodies:
        ordered.append(body)
        ordered.extend(sorted(w for w in ids if world_index[w].get('parent') == body))
    return ordered


def make_generated_world(rng, system, slot, n, zone, cls, base, primary, xenos, known_names):
    spec = GEN_CLASSES[cls]
    name = f'{base} {ROMAN[slot] if slot < len(ROMAN) else slot}'
    if name.lower() in known_names:
        name = f'{name} Minoris'
    known_names.add(name.lower())

    biome = spec['biome']
    surface_index = rng.randrange(len(spec['surface']))
    if cls == 'death':
        biome, surface_index = rng.choice(DEATH_VARIANTS)
    surface = spec['surface'][surface_index]

    low, high = POPULATION[cls]
    population = 0 if high == 0 else math.exp(rng.uniform(math.log(low), math.log(high)))
    notes = rng.choice(spec['notes'])
    if cls in ('dead', 'ice', 'scorched') and rng.random() < 0.2:
        notes += ' A small research station keeps a few hundred personnel here.'
        population = rng.randint(80, 900)

    t_low, t_high = TEMPERATURE[zone]
    temperature = rng.uniform(t_low, t_high)
    if cls == 'death' and biome == 'ice':
        temperature = rng.uniform(-70, -20)
    if cls == 'death' and biome == 'desert':
        temperature = rng.uniform(35, 70)

    if xenos:
        affiliation = f'Unclaimed; lies in a {faction_label(primary["faction"])} system'
        faction = 'unknown'
    elif cls in ('scorched', 'dead', 'ice', 'gas'):
        affiliation = 'Uninhabited; charted by the Imperium'
        faction = 'unknown'
    elif cls == 'forge':
        affiliation = 'Adeptus Mechanicus'
        faction = 'mechanicus'
    else:
        affiliation = 'Imperium'
        faction = 'imperium'

    label = spec['label'] + (f' ({spec["variant"]})' if spec.get('variant') else '')
    return {
        'id': f'gen-{system["id"].removeprefix("sys-")}-{slot}',
        'name': name,
        'generated': True,
        'location_kind': 'gas_giant' if cls == 'gas' else 'planet',
        'world_type': label,
        'class_key': cls,
        'class_code': spec['code'],
        'biome': biome,
        'faction': faction,
        'affiliation': affiliation,
        'surface': surface,
        'atmosphere': rng.choice(spec['atmosphere']),
        'notable': notes,
        'population': round(population),
        'population_label': format_population(population) if population >= 1000 else
                            ('None' if population == 0 else f'~{round(population)} personnel'),
        'tithe_grade': TITHE[cls],
        'gravity_g': None if cls == 'gas' else round(rng.uniform(0.35, 1.9), 2),
        'cloudtop_gravity_g': round(rng.uniform(0.9, 2.6), 2) if cls == 'gas' else None,
        'day_hours': None if cls == 'scorched' and rng.random() < 0.5 else round(rng.uniform(9, 62), 1),
        'tidally_locked': cls == 'scorched',
        'mean_temp_c': round(temperature),
        'moons': rng.randint(2, 28) if cls == 'gas' else rng.choice([0, 0, 0, 1, 1, 2, 3]),
        'orbit_zone': zone,
        'slot': slot,
        'system': system['id'],
        'sector_id': system.get('sector_id'),
        'segmentum': primary.get('segmentum'),
    }


if __name__ == '__main__':
    main()
