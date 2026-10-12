"""Source-audited corrections and later A-Z planet entries, 2026-10-12.
Official references not checked: source-tier remains wiki index only.
"""
from pathlib import Path
import json,csv,re,zipfile,collections
R=Path('/mnt/data/warhammer40k_atlas')
d=json.loads((R/'atlas_data.json').read_text('utf8'))
world=d['locations'];by={w['name'].casefold():w for w in world};byid={w['id'] for w in world};secids={s['id'] for s in d['sectors']}
P='https://wh40k.lexicanum.com/wiki/List_of_planets'
B='https://wh40k.lexicanum.com/wiki/Baal'
slug=lambda s:re.sub('[^a-z0-9]+','-',s.lower()).strip('-')
DATA='''
Kalighast IV|Ice World|||
Kaliman IV|Unclassified|||
Kalimant|Xenos World|||Hrud nest
Kallash|Feudal World|||
Kalleth|Destroyed World|Ultima|nostramo|Destroyed during M31
Kallista|Industrial World|||
Kalmatir|Unclassified|||
Kalor III|Unclassified|||
Kalto|Agri World|Obscurus|askellon|
Ka'mais|Former T'au Sept / Dead World|Ultima||
Kanak|Feral / Death World; former Tomb World|Obscurus||Kanak Skull Takers homeworld
Kane's Sorrow|Death World|Ultima||
Kantim Secondus|Unclassified|||
Kanzuz IX|Unclassified|Obscurus||Desecrated by Fabius Bile
Kao-li|Forbidden World|Obscurus|calixis|
Kapellis IX|Unclassified|||
Kappa Veldt|Unclassified|||
Kar Duniash|Segmentum Fortress|Ultima||Ultima Segmentum command center
Karacallia|Gas Giant|Obscurus|calixis|
Karadox|Unclassified|||
Karesh|Unclassified|||
Karis Cephalon|Unclassified|||
Karkariad|Hive World|Pacificus||Occupied by Chaos at one point
Karnak II|Unclassified|Obscurus||Lightning STC patterns discovered
Karnat|Unclassified|||
Karnax 17|Unclassified|||
Karrik|Ice / Death World|Obscurus||
Karygpha|War / Industrial World|||
Kasr Fuul|Unclassified|||
Kataris|Dead World; former Agri World|Obscurus||
Kathalon|Daemon World|Obscurus||
Kathur|Shrine World|Obscurus||
Kato|Shadow World|Ultima||
Kattyak|Unclassified|||
Kaurava I|Ork World; former Civilised World|Ultima|lithesh|
Kaurava II|Ork World; former Civilised World|Ultima|lithesh|
Kaurava III|Ork World; former Tomb World|Ultima|lithesh|
Kaurava IV|Unclassified|Ultima|lithesh|
Seco|Kroot Xenos World|Ultima||Kroot planet found during Third Sphere of Expansion
Seculoris|Unclassified|||
Secunda|Desert World|Obscurus||
Seedworld AFG:218|Forbidden World|Obscurus|calixis|
Seidon|Tomb World|Ultima||
Sekel's Landing|Unclassified|Solar||
Sekmet|Gas Giant|Obscurus|calixis|
Semmel|Unclassified|Ultima|vidar|
Semus|Unclassified|||
Sepharis Ultra|Unclassified|||
Sepheris Secundus|Feudal World|Obscurus|calixis|
Sepus Prime|Dead World|Pacificus||Destroyed via virus bombing
Seraphina|Former Ork World|Ultima||
Serena|Pleasure World|Obscurus|calixis|
Sergatama VI|Unclassified|||
Settlement 228|Frontier World|Obscurus|calixis|
Setvan|War World|Obscurus||
Sevara|Feral / Jungle World; former Hive World|||
Sevayin|Unclassified|||
Sha'draig|T'au Sept / Jungle / Death World|Ultima||
Shangh VI|Unclassified|||
Shannon's Reach|Unclassified|||Lawless world
Shardenus|Hive World|||
Sharlor|Agri World|||
Shau'Nesh|Former T'au Sept World|Ultima||
Shemnoch|Former Tomb World|||
Sheol XVII|Penal World|Obscurus|calixis|
Shodrax|Unclassified|||
Shroud|Ice World|||
Sibb's World|Unclassified|||
Sickle|Forbidden World|Obscurus|calixis|
Siculi|Agri World|Obscurus|calixis|
Sigma|Dead World|Ultima||
Sigma-Agrius|Agri World|Obscurus||
T'ruen|T'au-held World|||Attacked by Tyranid Hive Fleet Eumenides
Tabor|Ocean / Hive World|Obscurus|agripinaa|
Tabulata|Unclassified|||
Taeloth|Uninhabited World|Obscurus||
Tagia Prime|Unclassified|||
Tahnel|Civilised / Ocean World|Solar||
Talasa Prime|Adeptus Astartes / Inquisitorial Fortress World|Ultima||Deathwatch headquarters
Talassar|Civilised / Ocean World|Ultima|ultima|Ultramar
Talithia|Maiden World|||Former human colony returned to Aeldari
Tallameder|Unclassified|||
Tallarn|Desert / Civilised World|Tempestus||
Ta-Loc|Quarantined World|Ultima||Signus Cluster
Taloma Nova|Unclassified|||
Talon|Dead World; former Astartes Homeworld|Ultima||
Talsicant|Unclassified|||
Talus IV|Former Astartes Homeworld|Obscurus||
Tan|Dead World|Ultima||Scoured by Hive Fleet Kraken
Tanakreg|Dead World; former Civilised World|||
Tancred|Unclassified|Obscurus||
Tandria|Shrine World|Ultima|cirillo|
Tanhotep|Tomb World|||
Tanith|Dead World; former Forest World|Pacificus||
Tannen's World|Unclassified|||
Taral III|Unclassified|||
Taran III|Astartes Homeworld|||Storm Warriors Chapter
Taranagea|Unclassified|||
Tarentus|Agri World|Ultima|ultima|Ultramar
Tareska|Unclassified|Ultima||
Tysseris|Unclassified|Ultima||Near the Ghoul Stars
U-6743|Unclassified|||
UB-26|Death World|||
Ugmok's World|Former Ork World|||Invaded by Nurgle daemons in M42
Ularis Prime|Unclassified|||
Uldan|Mining / Jungle World|||
Ullden|Former Agri World|||
Ultak|War / Hive World|||
Ultra Maximus|Contested Human World|Ultima||Temporarily held by T'au
Ultra Mundanus|Unclassified|Ultima||
Umbador|Agri World|||
Umbrus|Unclassified|Obscurus||
Unloth|Feral World|||
Unspake|Fortress World|Pacificus||
Uolesh|Daemon World|Obscurus||
Upsilon|Fortress World|Solar||Defensive bastion of Terra
Ur-Clemait|Human / T'au World|Ultima||Human world under T'au control
Ur-Haven|Unclassified|||
Uralan|Unclassified|Obscurus||
Uralek Prime|Civilised World; former Exodite World|Ultima||
Urdek|Former Maiden World|||Imperial settlement after Aeldari world
Urdesh|Forge World|Pacificus||Sabbat Worlds
Urkrask|Unclassified|||
Urmuk|Ork Industrial World|Ultima|octarius|
Urrghaz|Unclassified|||
Urus|Unclassified|Pacificus||Sabbat Worlds
Uttu Prime|Former Imperial / Necron World|Ultima||Absorbed into Sautekh Dynasty late M41
Uvander|Unclassified|||
Uzarn|Unclassified|||
Vakon Alpha|Ice World|||Vakonian Winter Wars
Valedor|Destroyed Civilised World|Tempestus||Destroyed by Fireheart device
Vallyx V|Death World|Ultima||
Valon Urr|Shrine World|Obscurus|calixis|
Valos|Dead World|Ultima||
Valos Krin|Feral World|Obscurus|calixis|
Valskalf|Squat World|||
Vanaheim|Forge World|||
Vanantis IX|Hive World|||
Vander's Landing|Agri World|Obscurus||
Vanishpoint|Ice World|||
Vanqualis|Hive World|||
Vardan|Imperial World|||Vardan Rifles homeworld
Verdant|Abhuman World|||Troth abhumans
Verdfall|Unclassified|Pacificus||
Verdus Prime|Tomb World|||
Verghast|Hive / Industrial World|Pacificus||
Veridanium|Maiden World|||Former Imperial colony, reclaimed by Aeldari
Veridian|Feral World|Ultima||
Verity|Dead World|Solar||
Vernalis|Mining World|Obscurus||
Veskepine|Jungle World|||
Vespertine|Unclassified|||
Vessos|Unclassified|||
Vetrim|Former T'au bond-world|||
Vhomarl|Unclassified|||
Vhospis|Feudal World|||
Vhun|Unclassified|||
Victrix Sonora|Agri World|Solar||
Victus|Dead World|Obscurus||
Vidar|Unclassified|Ultima||
Vigil|Dead World|Obscurus||
Vimox|Unclassified|||
Virger-Mos II|Agri World|Ultima||
Viribius|Feral World|Obscurus|calixis|
Viridia IV|Agri World|||
Virmerketh|Unclassified|||
Vitrea Mundi|Former Astartes Homeworld|Ultima||
Vohyd|Nomad World|Pacificus||
Volchis IV|Unclassified|||
Voldarian II|Unclassified|||
Volghast|Unclassified|||
Volonx|Feral World|Obscurus|calixis|
Volscar|Unclassified|Obscurus||
Voltemand|Civilised World|Pacificus||
Volturn|Civilised World|Pacificus||
Voluptua|Shrine World|Obscurus|calixis|
Vonsha Smyde IX|War World|Ultima||
Vorakis|Hive World|||In Imperium Nihilus
Vorenz-VI|Penal World|||
Vorg Prime|Unclassified|||
Vorgundreel|Agri World|||
Vorlanthus IV|Hive World|||
Voth|Unclassified|||
Vouxis Prime|Civilised World|Obscurus|askellon|
Vraks Prime|Armoury World|Obscurus||Under Imperial interdiction
Vrantis III|Industrial World|||
V'run|Ork World|Tempestus||
Vulcron|War / Mining World|||Mining-damaged crust
Vulkard IV|Volcanic World|Ultima||
Vuthulea II|Unclassified|||
Warzone Epsilon|War World|Obscurus|calixis|
Wezn|Ice World|||
Wichard|Unclassified|||
Windhover|Unclassified|||
Winterhome IX|Ice World|Obscurus||
Woe|Death World|Obscurus|calixis|
World of Immortal Sorrows|Daemon / Crone World|Obscurus||
Wormgyre|Xenos World|Pacificus||Hellgrammite origin world
Youlemesesh|Maiden World|||
Yrnax|Unclassified|||
Ysai Ydumee|Frontier World|Obscurus|calixis|
Yspotua|Former Paradise World|||
Ystrad|Dead World|||Exterminatus to slow Tyranids
Yue|Desert World|||
Yu'Kanesh|Desert World|||
Yulan|Dead World|Ultima||
Yundo|Unclassified|||
Yyem|Unclassified|||
Zaga IV|Unclassified|Pacificus||
Zaebus Minoris|Astartes / Feral World|Tempestus||Red Scorpions homeworld
Zakhinta|Unclassified|||
Zalamis|Unclassified|||
Zambeque|Unclassified|Obscurus||
Zantium|Unclassified|||
Zantragora|Tomb World|Ultima||
Zaramund|Unclassified|Obscurus||
Zarthan VII|Tomb World|||
Zavamunda|Unclassified|||
Zel Primus|Unclassified|Obscurus|calixis|
Zel Secundus|Death World|Obscurus|calixis|
Zel Tertius|Frontier World|Obscurus|calixis|
Zepetis VII|Unclassified|||
Zephath|Unclassified|Ultima||Ultramar border
Zephyr|Astartes Homeworld|Obscurus||Storm Hawks homeworld
Zeus VI|Agri World|||
Zhodon|Unclassified|||
Zhoros|Dead World; former Astartes Homeworld|||Fire Hawks homeworld, destroyed M36
Zibal|Desert World|||
Zillman's Domain|Feudal World|Obscurus|calixis|
Zoran|Ice World|||
Zordion|Desert / Death World|||Imperium Nihilus
Zumthor|Frontier World|Obscurus|calixis|
Zurna|Unclassified|Ultima|vidar|
Zweihan's World|Hive World|Obscurus|calixis|
'''.strip()
added=0;existing=0
for line in DATA.splitlines():
 if not line.strip():continue
 a=line.split('|')
 if len(a)!=5:raise ValueError(('bad columns',a))
 name,typ,seg,sector,note=a
 if name.casefold() in by:
  w=by[name.casefold()];existing+=1
  # If index states a more specific planetary type than generic unknown, adopt only for index-only records
  if w.get('factsheet_completeness')=='index_only' and w['world_type'] in ['Unclassified','Forge World'] and typ!='Unclassified':
   if w['world_type']=='Unclassified' or ('Forge' in typ):w['world_type']=typ
  w.setdefault('indexed_attestations',[])
  if P not in w['indexed_attestations']:w['indexed_attestations'].append(P)
  if sector and not w.get('sector_id') and slug(sector) in secids:w['sector_id']=slug(sector)
  if seg and not w.get('segmentum'):w['segmentum']=seg
  if note and note not in w['notable']:w.setdefault('source_notes',[]).append({'source':P,'note':note})
  continue
 ident=slug(name)
 if ident in byid:ident+='-named-world'
 ss=slug(sector) if slug(sector) in secids else None
 kind='gas_giant' if typ=='Gas Giant' else 'planet'
 w={'id':ident,'name':name,'location_kind':kind,'segmentum':seg or None,'sector_id':ss,'world_type':typ,
 'affiliation':'Unspecified; no definitive era-specific owner verified','surface':'Unknown; not documented in reviewed reference.',
 'atmosphere':'Unknown; not documented in reviewed reference.','notable':note or 'Named in Lexicanum planet index.',
 'source_url':P,'source_tier':'Lexicanum secondary index, primary source needs review','source_list_url':P,
 'review_state':'index_only','eye_relation':'unknown','rift_side':'unknown','position':None,'era_status':{'pre_eye':'Unknown','pre_rift':'Unknown','post_rift':'Unknown'},'history':[],
 'system_id':None,'subsector_id':None,'factsheet_completeness':'index_only','environment_evidence':'unknown',
 'coordinates_verified':False,'planet_position_source':None,'time_scope':'unspecified','indexed_attestations':[P]}
 world.append(w);by[name.casefold()]=w;byid.add(ident);added+=1
# Verified type and segmentum corrections from planetary index cross-check
vespid=by.get('vespid')
if vespid:
 vespid['location_kind']='gas_giant';vespid['world_type']='Vespid Homeworld / Gas Giant'
 vespid['notable']='Homeworld of the Vespid species; source explicitly classifies the celestial body as a gas giant and a T’au Empire member world.'
 vespid['surface']='Gas giant: no conventional solid terrestrial surface established. Habitation ecology unverified.'
 vespid['atmosphere']='Extensive gaseous envelope; specific composition and breathable levels unverified.'
 vespid['environment_evidence']='celestial_type_documented_specific_chemistry_unknown'
 vespid['source_url']=P;vespid['indexed_attestations']=[P]
 for h in d.get('faction_homeworlds',[]):
  if h['faction']=='Vespid':h['body_kind']='gas_giant';h['notes']='Vespid species homeworld is classified as a gas giant; atmospheric layers require deeper source review.';h['source_url']=P
vost=by.get('vostroya')
if vost:
 vost['segmentum']='Obscurus';vost['geography_note']='Corrected from Solar to Obscurus after comparison with Lexicanum planetary index.'
 vost.setdefault('indexed_attestations',[]).append(P)
for nm in ['Baal','Baal Primus','Baal Secundus']:
 w=by.get(nm.casefold())
 if w:
  w.setdefault('indexed_attestations',[]).append(B)
  if nm=='Baal':
   w['physical_properties']={'orbital_distance_au':3.4,'surface_gravity_earth':1.27,'mean_temperature_c':12,'source_url':B,'source_status':'as listed in secondary entry; date and original references require confirmation'}
   w['historical_environment']='Baal and two moons were more habitable before the Age of Strife; warfare caused radiological devastation.'
  elif nm=='Baal Primus':
   w['era_status']['post_rift']='Rendered barren in the Devastation of Baal; subsequent bombardment destroyed daemon markings.'
   w['surface']='Formerly devastated terrain; rendered barren during the Devastation of Baal.'
  else:
   w['era_status']['post_rift']='Badly damaged by Tyranid assault; site of Sanguinius’s landing remains historically important.'
   w['atmosphere']='Toxic/radiation-affected surface conditions reported; precise atmospheric mixture unknown.'
# Historical alias not a new independent planet: now Mekslag-Ikks was Kastorel-Novem per published index
mek=by.get('mekslag-ikks')
if mek:
 mek.setdefault('aliases',[])
 if 'Kastorel-Novem' not in mek['aliases']:mek['aliases'].append('Kastorel-Novem')
 mek['world_type']='Ork World; former Mining World'
 mek['notable']='Formerly the Imperial mining world Kastorel-Novem, later taken by Orks and renamed Mekslag-Ikks; listed as a Waaagh! Garaghak base.'
 mek.setdefault('indexed_attestations',[]).append(P)
 if mek['segmentum']!='Ultima':
  mek['geography_conflict']='Lexicanum planet index places Kastorel-Novem in Ultima; previously seeded Mekslag-Ikks in Tempestus/Forsarr. These require individual article source review.'
  mek['segmentum']=None;mek['sector_id']=None
# Separate identity collision: Lexicanum list contains two distinctly classified planets named Tanis.
d.setdefault('same_name_different_planets',[]).append({'name':'Tanis','classification_1':'Desert World / Astartes recruiting world','classification_2':'Quarantined World; former Hive World','source_url':P,'editorial_status':'different rows; do not automatically merge; verify identity and setting'})
# Further possible aliases: user needs merge control rather than independent markers
for pair in [{'a':'Mekslag-Ikks','b':'Kastorel-Novem','relation':'confirmed historical renaming from cited index'}]:
 d.setdefault('potential_duplicates_and_aliases',[]).append(pair)
d['version']='0.7-late-alphabet-index-plus-qa-2026-10-12'
d['coverage']['named_location_rows']=len(world)
d['coverage']['index_only_locations']=sum(w.get('factsheet_completeness')=='index_only' for w in world)
d['coverage']['named_gas_giants']=sum(w['location_kind']=='gas_giant' for w in world)
d['coverage']['known_potential_name_collisions']=len(d['potential_duplicates_and_aliases'])
d['source_specific_limitations'].append('The general list contains multiple Tanis records; shared strings are not proof of same world')
# Rewrite using same strongly typed export routines
(R/'atlas_data.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
def csvout(file,rows):
 cols=list(dict.fromkeys(k for r in rows for k in r))
 with (R/file).open('w',newline='',encoding='utf-8-sig') as f:
  wr=csv.DictWriter(f,fieldnames=cols);wr.writeheader()
  for r in rows:wr.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
for f,rows in [('locations.csv',world),('sectors.csv',d['sectors']),('subsectors.csv',d['subsectors']),('systems.csv',d['systems']),('faction_homeworlds.csv',d['faction_homeworlds']),('possible_aliases.csv',d['potential_duplicates_and_aliases']),('same_name_conflicts.csv',d['same_name_different_planets'])]:csvout(f,rows)
audit=[]
for w in world:
 a=w.get('atmosphere','');s=w.get('surface','')
 audit.append({'name':w['name'],'location_kind':w['location_kind'],'source':w['source_url'],'index_source':w.get('source_list_url') or '',
 'type':w['world_type'],'sector_id':w['sector_id'] or '','segmentum':w['segmentum'] or '',
 'review_state':w['review_state'],'factsheet_completeness':w.get('factsheet_completeness','curated_partial'),
 'atmosphere_known':not a.lower().startswith(('unknown','unspecified','not consistently','enclosed artificial','extensive gaseous')),
 'surface_known':not s.lower().startswith(('unknown','unspecified','artificial habitat')),
 'coordinates_known':w.get('coordinates_verified',False),'eye_relation':w['eye_relation'],'rift_side':w['rift_side'],
 'indexed_attestations':' ; '.join(w.get('indexed_attestations',[]))})
csvout('source_audit.csv',audit)
app=(R/'atlas_template.html').read_text('utf8')
app=app.replace('an offline, curated starter catalog','an offline, expanded but incomplete lore index')
app=app.replace("const kindLabel={planet:","const kindLabel={artificial_habitat:'Artificial habitat',planet:")
app=app.replace("/^(Unspecified\\.?|Not consistently)/i.test(w.atmosphere)","/^(Unspecified\\.?|Not consistently|Unknown|Enclosed artificial habitats|Extensive gaseous)/i.test(w.atmosphere)")
app=app.replace('__ATLAS_JSON__',json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
(R/'atlas.html').write_text(app,'utf8')
readme=(R/'README.md').read_text('utf8')
readme=re.sub(r'\*\*\d+\*\* unique named planet, moon, habitat and other location records',f'**{len(world)}** unique named planet, moon, habitat and other location records',readme)
readme=re.sub(r'\*\*\d+\*\* additional `index_only` location records with skeletal factsheets;',f'**{d["coverage"]["index_only_locations"]}** additional `index_only` location records with skeletal factsheets;',readme)
readme=re.sub(r'Current total is \*\*\d+\*\* individually named location rows',f'Current total is **{len(world)}** individually named location rows',readme)
readme+='\n## Fourth pass: corrections and late alphabet planets\n\nFurther manual transcription from K–Z sections of the [Lexicanum planet index]('+P+') added **'+str(added)+'** previously unlisted locations. Corrections: Vespid is a gas giant, Vostroya is listed in Obscurus, Mekslag-Ikks has the historical name Kastorel-Novem, and Baal has separately sourced orbital/gravity data. See `same_name_conflicts.csv` for multiple different planets with identical printed names. **The atlas is still incomplete**; these are samples rather than all index rows.\n'
(R/'README.md').write_text(readme,'utf8')
zipname=Path('/mnt/data/warhammer40k_galactic_atlas_expanded.zip')
files=['atlas.html','atlas_data.json','locations.csv','sectors.csv','subsectors.csv','systems.csv','source_audit.csv','faction_homeworlds.csv','possible_aliases.csv','same_name_conflicts.csv','tau_sept_systems.csv','primarch_homeworlds.csv','README.md','atlas_template.html','enrich_research.py','enrich_factions.py','enrich_late_index.py','build.py']
with zipfile.ZipFile(zipname,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(R/f,arcname='warhammer40k_atlas/'+f)
print(json.dumps({'added_late_index':added,'existing_crossindexed':existing,'locations':len(world),'zip_size':zipname.stat().st_size,'sources':len(d['sources'])},indent=2))
