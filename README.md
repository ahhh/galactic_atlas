# Warhammer 40,000 Galactic Atlas — Research Expansion

## Indexed coverage as of 12 October 2026

- **139** sector and distinct named region records (not all true Imperial sectors)
- **123** subsectors and other named subregions
- **34** star-system records
- **1077** unique named planet, moon, habitat and other location records
- **944** additional `index_only` location records with skeletal factsheets; **133** edited seed factsheets
- 20 Primarch homeworld lines, including deliberately unresolved entries
- **No** real-space canonical coordinates claimed and **no** claim of completeness.

## Files

- `atlas.html`: self-contained interactive viewer with era overlays, sector and location search, factsheets, and JSON/CSV exports. Open locally in a browser.
- `atlas_data.json`: canonical editable project database.
- `sectors.csv`, `subsectors.csv`, `systems.csv`, `locations.csv`: machine-readable hierarchy.
- `source_audit.csv`: review queue with index-only/curated states, source URL, missing atmosphere and map position flags.
- `faction_homeworlds.csv`: distinguishes true central planets, distributed homeworlds, and nonplanet capitals.
- `possible_aliases.csv`: unresolved suspected duplicate world and edition-spelling pairs.
- `tau_sept_systems.csv`: named T'au septs that should **not** automatically be treated as planetary bodies.
- `primarch_homeworlds.csv`: primarch/world lookup, moon and unknown notes retained.

## How this pass was researched

The Lexicanum [sector index](https://wh40k.lexicanum.com/wiki/List_of_sectors), [planet index](https://wh40k.lexicanum.com/wiki/List_of_planets), [Necron tomb world index](https://wh40k.lexicanum.com/wiki/Tomb_World), and [Tau sept list](https://wh40k.lexicanum.com/wiki/Sept_Symbol) were checked on 2026-10-12. Some source-linked index entries have uncertain citation status; source-level review is pending. For any record drawn only from an index, attributes are explicitly unknown unless specified in that index. Desert/ocean/ice etc. surface descriptions are **only interpretations of the stated WORLD TYPE**, not separately verified environmental facts. In particular, climate/chemical atmosphere is *not* deduced from a general world type.

`Sectors` include several comparable-looking **regions, reaches, cluster names and border sectors**; consult `category`. Some sector/segmentum assignments change with editions or are unsettled, e.g. Fenris in some sources, and Stygius near the Obscurus/Ultima border. A few named locations are station/rift descriptions and should not be plotted as physical planets; such entries are separately typed or omitted.

## Accuracy and remaining work

These are deliberately **indexed, not exhaustive**. The general planet list currently spans over 3,000 rendered lines of entries and sources and we did not transcribe every line; many additional planets still remain. Even recording every name in an article is not 'all planets' in-universe. Prioritize broad A–Z harvesting with pagination-aware licensed ingestion, deduplicate renamed worlds, identify planet vs station/ship/moon, traverse category pages and sector-specific gazetteers, and check original GW/FW/Black Library/FFG books for every atmosphere, surface, sovereign date and faction. Many entries will never have a fully specified atmosphere. Scientific simulation must remain optional and clearly non-canonical.

For maps, only plot coordinates whose source and reference frame are documented. The Eye of Terror dates to the Fall of the Aeldari, while the Cicatrix Maledictum follows the 13th Black Crusade. Preserve historical identity rather than inventing previous eye/warp Rift states of worlds.

Unofficial fan-made research project. Warhammer 40,000 © Games Workshop. Summaries are paraphrased and sources linked; no prose from reference articles copied into database in bulk.

## Third pass: faction indexes

Research added the [Forge World index](https://wh40k.lexicanum.com/wiki/Forge_worlds), [Aeldari Craftworlds](https://wh40k.lexicanum.com/wiki/List_of_Craftworlds), and [Ork Domains](https://wh40k.lexicanum.com/wiki/Ork_Domains), with a first sample from the [Knight World index](https://wh40k.lexicanum.com/wiki/Knight_World). Current total is **1077** individually named location rows including **81** craftworlds.

World classifications and names in these indexes were recorded without manufacturing planet-specific atmosphere or terrain descriptions. Some records in published indexes are moons or artificial habitats, while some same-name hits are historical alterations or independent names; see `possible_aliases.csv`. World count is *not* number of inhabited natural planets. Source index coverage is partial, primarily for planet list letters after the initial section.

## Fourth pass: corrections and late alphabet planets

Further manual transcription from K–Z sections of the [Lexicanum planet index](https://wh40k.lexicanum.com/wiki/List_of_planets) added **216** previously unlisted locations. Corrections: Vespid is a gas giant, Vostroya is listed in Obscurus, Mekslag-Ikks has the historical name Kastorel-Novem, and Baal has separately sourced orbital/gravity data. See `same_name_conflicts.csv` for multiple different planets with identical printed names. **The atlas is still incomplete**; these are samples rather than all index rows.

## Web atlas (`index.html`)

An interactive galaxy browser modelled on the Real Universe Explorer: a full-screen 3D map with a world browser on the left, an info card on the right and a status bar. It is a static site with no build step and no backend, so it can be hosted on GitHub Pages as it is.

**Galaxy → star system → world.** Search or pick a world and the view flies across the galaxy to its system, crosses into the system view and opens the world's info card. *View world close up* shows a procedural surface. The Pre-Fall / M41 / M42 switch toggles the Eye of Terror and the Great Rift, and highlights the matching era record on each card. Shareable links: `?world=cadia`, `?system=solar-sol&view=system`, `?sector=calixis`, `?segmentum=Ultima`, `?feature=great_rift`, `&era=post_rift`.

### Every world is placed, and every placement is explained

The corpus records no coordinates (`verified_coordinates: 0`), so `scripts/build_atlas.py` gives each of the 1,077 records a best-guess position on a flat galactic plane (kly, galactic core at the origin, Terra at 6 kly W and 10 kly S). The first rule that applies wins:

| Method | Records | Confidence |
|---|---|---|
| Hand-placed from the published maps (Terra, Cadia, Baal, Macragge, T'au…) | 60 | Approximate |
| Shares a recorded star system, or a name like *Zel Primus / Zel Secundus* | 55 | Approximate |
| Inside its recorded subsector or sector | 196 | Approximate |
| A place name in its notes ("Ultramar", "Koronus", "Hive Fleet Leviathan"…) | 19 | Best guess |
| Random within its recorded segmentum | 167 | Best guess |
| Random within its faction's region (craftworlds on the rim, Ork empires, tomb worlds in the outer galaxy, Chaos near the Eye) | 174 | Best guess |
| Random in Imperial space (nothing recorded at all) | 406 | Best guess |

Each info card shows the method, the confidence and a one-line reason. Estimated values carry an amber **Estimated** badge, and a segmentum or Great Rift side that is inferred from the position rather than recorded is badged the same way. A recorded segmentum is never overridden: scatter and place-name hints that would cross a recorded border are rejected.

### Undocumented worlds

Systems the corpus names only one or two bodies in are filled out with **6,229 generated worlds**. Each system gets 4–11 orbits, and documented worlds keep their numerals (Ophelia VII sits in the 7th orbit). The class mix follows the Imperial survey pattern. About 75% are dead or uninhabitable worlds and gas giants. The rest are mostly mining, death, civilised, penal, feral, agri and feudal worlds (in rough order), with a few shrine worlds and rare forge and hive worlds. Inner orbits run to scorched rock, outer orbits to gas giants and ice. Systems held by xenos or Chaos get no Imperial filler. Every generated world has its own card (classification and class code, population, tithe grade, gravity, day length, temperature, moons, surface, atmosphere and a survey note), all badged **Generated** under a banner saying it is invented. Generated worlds use dashed orbits and italic labels, are hidden from the world list by default (*Filters → Records*), and can be hidden from systems under *Layers*. The Sol System is not padded.

### Running and rebuilding

```bash
python3 -m http.server 8000      # then open http://localhost:8000
python3 scripts/build_atlas.py   # regenerate data/atlas.json after editing atlas_data.json
```

The page fetches `data/atlas.json`, so it must be served over HTTP. Opening the file directly from disk will not work. To publish, push the folder to a GitHub repository and enable Pages from the branch root; `.nojekyll` is included. The Three.js build is vendored in `vendor/`, so nothing loads from a CDN except the Google Fonts.

```
index.html           page shell
styles/app.css       interface styling
src/app.js           wiring, flights, render loop
src/galaxy-view.js   disc, segmenta, sectors, warp storms, system markers
src/system-view.js   schematic star systems
src/planet-view.js   procedural world surfaces, craftworld/station models
src/inspector.js     info-card content
src/ui.js            browser, filters, card renderer, status bar
src/search.js        ranked search
src/navigation.js    breadcrumbs and URL state
data/atlas.json      generated by scripts/build_atlas.py
```
