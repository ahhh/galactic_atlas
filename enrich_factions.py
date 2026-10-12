"""Third pass: add verified index-attested faction worlds, preserve historical and identity ambiguity.
Indexes checked 2026-10-12; PRIMARY published citations remain follow-up work.
"""
import json,csv,re,collections,zipfile
from pathlib import Path
from urllib.parse import quote
R=Path('/mnt/data/warhammer40k_atlas')
d=json.loads((R/'atlas_data.json').read_text('utf8'))
wlist=d['locations']; sectors=d['sectors']; subs=d['subsectors']; systems=d['systems']
F='https://wh40k.lexicanum.com/wiki/Forge_worlds'
C='https://wh40k.lexicanum.com/wiki/List_of_Craftworlds'
O='https://wh40k.lexicanum.com/wiki/Ork_Domains'
K='https://wh40k.lexicanum.com/wiki/Knight_World'
slug=lambda n:re.sub(r'[^a-z0-9]+','-',n.casefold()).strip('-')
byname={x['name'].casefold():x for x in wlist}
byids={x['id'] for x in wlist}
counts=collections.Counter()

def add(name,typ,kind,affiliation,src,note=None,segmentum=None,sector=None,history_note=None,aliases=None):
    key=name.casefold()
    if key in byname:
        x=byname[key]
        attest=x.setdefault('indexed_attestations',[])
        if src not in attest:attest.append(src)
        # No overwriting curated details / world type or temporal control when source is an index
        if x.get('world_type') not in [typ] and not x.get('factsheet_completeness')=='curated_partial':
            x.setdefault('classification_alternates',[])
            if typ not in x['classification_alternates']:x['classification_alternates'].append(typ)
        if note and note not in x.get('notable',''):
            x.setdefault('source_notes',[]).append({'source':src,'note':note})
        counts['existing_attested']+=1
        return x
    ident=slug(name)
    if ident in byids:
        ident=f'{ident}-{slug(kind)}'
    if ident in byids:raise ValueError(('dup ID',name))
    if sector and slug(sector) not in {s['id'] for s in sectors}:sector=None
    x={'id':ident,'name':name,'location_kind':kind,'segmentum':segmentum,'sector_id':slug(sector) if sector else None,
       'world_type':typ,'affiliation':affiliation,'surface':'Unknown; not documented in reviewed reference.',
       'atmosphere':'Unknown; not documented in reviewed reference.','notable':note or 'Named in faction world/craftworld index; environmental description not independently verified.',
       'source_url':src,'source_tier':'Lexicanum secondary index; underlying primary source review pending',
       'source_list_url':src,'review_state':'index_only','eye_relation':'unknown','rift_side':'unknown','position':None,
       'era_status':{'pre_eye':'Unknown','pre_rift':'Unknown','post_rift':'Unknown'},'history':[],
       'system_id':None,'subsector_id':None,'factsheet_completeness':'index_only','environment_evidence':'unknown',
       'coordinates_verified':False,'planet_position_source':None,'time_scope':'unspecified',
       'indexed_attestations':[src]}
    if history_note:x['historical_note']=history_note
    if aliases:x['aliases']=aliases
    wlist.append(x);byname[key]=x;byids.add(ident);counts[kind]+=1
    return x

CRAFT='''Aestheria-Anaris|Alaitoc|Altansar|Alurmen|An-Iolsus|Anuiven|Aon'tai|Arach-Qin|Aringhe|Bel-Shammon|Biel-Tan|Brae-Kaithe|Crudarach|Chto|Dolthe|Drohai|Elathec|Eyslk-Tan|Féin-Cineál|Furta-Rith|Idharae|Il'saraidh|Il-Kaithe|Ila-Manesh|Illisar|Ilmaren|Invincible|Iyanden|Iybraesil|Jai-Tan|Jielthwa|Kaelor|Kal'raktri|Kalth'se|Kher-Ys|Kinshara|Lan'edin|Lanimayesh|Lu'Nasad|Lugganath|Maegnár|Magc'Sithraal|Malan'tai|Mero|Meud-Wyaid|Miandrothe|Miel Carn|Mór-ríoh'i|Morwhe-Sheno|Muirgaythh|Mymeara|Mynathensar|Nacretineï|Nyatho|Nyo-Fae|Olhn-Tann|Os'tara|Riellen|Saim-Hann|Sethoywan|She'enshar|Shilea-Jar|Stel-Uit|Taial'shara|Telennar|Theminarae|Thuyelsa|Tir-Val|Tuathal|Tuonoetar|Ul-Khari|Ulthwé|Ulthwé-Na-Daan|Uthuriel|Varantha|X'amot|Yme-Loc|Zahr-Tann|Zaisuthra|Zandros|Zu'lasa'''.split('|')
DESTROYED=set('Alurmen Aon\'tai Bel-Shammon Crudarach Féin-Cineál Idharae Ila-Manesh Kalth\'se Kher-Ys Lanimayesh Lu\'Nasad Magc\'Sithraal Malan\'tai Mór-ríoh\'i Morwhe-Sheno Muirgaythh She\'enshar Taial\'shara Thuyelsa Tuonoetar Uthuriel X\'amot Zahr-Tann Zu\'lasa'.split('||')) # overwritten below explicitly
DESTROYED={'Alurmen',"Aon'tai",'Bel-Shammon','Crudarach','Féin-Cineál','Idharae','Ila-Manesh',"Kalth'se",'Kher-Ys','Lanimayesh',"Lu'Nasad","Magc'Sithraal","Malan'tai","Mór-ríoh'i",'Morwhe-Sheno','Muirgaythh',"She'enshar","Taial'shara",'Thuyelsa','Tuonoetar','Uthuriel',"X'amot",'Zahr-Tann',"Zu'lasa"}
CRASHED={'Theminarae':'Crashed on Quintus.', 'Ul-Khari':'Crashed on Trollius.'}
for name in CRAFT:
  note='Major Aeldari craftworld.' if name in {'Alaitoc','Biel-Tan','Iyanden','Saim-Hann','Ulthwé'} else 'Attested named Aeldari craftworld.'
  if name in DESTROYED:note+=' Listed as destroyed in source index; destruction date varies.'
  if name in CRASHED:note+=' '+CRASHED[name]
  if name in {'Mero','Drohai','Chto'}:note+=' Name/spelling is disputed across cited editions.'
  w=add(name,'Aeldari Craftworld','craftworld','Aeldari',C,note)
  if w.get('factsheet_completeness')=='index_only':
   w['surface']='Artificial habitat: interior biomes and structures; specific terrain unverified.'
   w['atmosphere']='Enclosed artificial habitats; gas composition and conditions unverified.'
   w['environment_evidence']='generic_craftworld_structure_not_specific_craftworld'
   if name in DESTROYED or name in CRASHED:w['era_status']['post_rift']='Historical loss or destruction reported; exact era must be checked in linked article.'
# Black Library is not an ordinary named planet/craftworld; legacy lore calls it a craftworld but status is contested.
add('Black Library','Aeldari mobile repository','artificial_habitat','Harlequins / Aeldari',C,
    'Source lists it among craftworlds; it is an extraordinary mobile repository protected by the Harlequins, not a conventional planet.')

FORGE='''Accatran|Achlys III|Adrosi|Agripinaa|Albert IV|Alpha Primus|Altevfor|Ammunheim|Amontep II|Angstrom|Antasic IX|Antax|Antioc|Anvillus|Anvilus Nine|Aphret|Appus IV|Arachnus|Arenxis Minoris|Arl'yeth|Artemia Majoris|Artos-Rho IV|Atanix Triumvirae|Atar-Median|Avachrus|Barnassus|Belacane|Bellicos|Bellona|Beshic V|Beta Cornix|Bheta-Decima|Branx Minor|Bronta-Median|Byrrus Alpha|Cadamine|Cadmon's Lock|Cahim II|Casiorix|Cavor Sarta|Chaeroneia|Columnus|Crucible-Omega|Cyclopea|Cyclothrathe|Cypra Mundi|Cyraxus II|Daiamantus|Dantris III|Daxxos|Delphi|Delphi IX|Demios Binary|Diamat|Diesos|Dominica II|Driantum|Duos|Dykurnos VI|Dynax Primus|Dynax-Abultra|Dynostix V|Ecovoria|Eontar|Ermune|Estaban III|Estaban VII|Esteban VII|Eufrates II|Ferrovarum|Forge Polix|Forge World Thule|Fortis Binary|Fusiria|Galatia|Gamanede|Gantz|Gehn Quora|Gharani|Ghoulwright|Glasgow IV|Glenescrede Raptus|Glomus|Goralech|Gorgonum|Gorvallon|Goth|Graia|Grammachus Beta|Gulgorahd|Gylax VI|Hadd|Haddrack|Halfus|Hekateus IV|Helios|Hellgrace|Hephaesto|Hervara|Hesh|Het|Hexium Minora|Hydra Cordatus|Hydraphur|Hypnoth|Idumea|Iktomia|Illium|Incaladion|Ionus X|Iridial|Ironfound|Ironghast Foundry|Ironhelm|Ixas|JXM A18Z|Kaedis Prime|Kai|Kalibrax|Kantakkha|Kantos|Kantrael|Kappa Prime|Kernak III|Khania|Kiavahr|Koden Tertius|Kogen's Toil|Konor|Krawbek|Krytos|Lankast|Lannar IV|Lashte|Lector's Lowell|Lentrel Prime|Lipitou Anville|Lliax|Lucius|M'khand|M'Pandex|Magnax|Magnos Omicron|Mediant|Megyre|Melior-Tertia|Mezoa|Milhand|Moirae|Monsk|Moredakka|Morod|Morvane|Mpandex|Nekkar|Ninevah|Noctillus Dhega-Nox|Novios|Nullivar|Nysairene Delta|Ohmn-Mat|Onos|Ophelia VII|Opus Ersaticus|Opus Macharius|Ordana|Ordex-Thaag|Orestes|Parabellus III|Pentos|Perinetus|Phaestos|Phaeton|Phaistos|Phoebe|Porphetus|Proteus|Proximus|Qartos|Qintos|Quir|Raeddon|Rangda IX|Retlaxi|Rho-Delpha|Ryboth|Samech|Sanctus Valorium|Sarcosa-Omikron|Sareme|Satyraes XII|Seixios|Septios|Shaehol|Shallethrax|Shenlong|Shern|Shevilar|Sidon 452|Sigma-Ulstari|Silent Forge|Skorgulian|Solemnium|Staban VII|Straxos|Stryken Primus|Stygia XII|Stygies VIII|Synford|Synford II|Taslan's Forge|Telemachus|Telerac|Temaxia|Tephusa Binary|Thagria|Thrax|Thrios|Thule|Tigrus|Titanslair|Toil|Tolkan|Tolkhan|Tophet VI|Transix Seven|Triplex Phall|Trisolian A-4|Turanshush|Tydeus|Tymatros Aleph|Ulan Huda|Vantius|Vastum-01|Vaznagrod|Vellung|Venatoria|Verica VII|Vindalex|Voss|Voss Prime|Weldcog|Xana|Xana II|Zeran|Zhao-Arkkad|Zopyrus VI|Zosma|Zpandex'''.split('|')
FORGE_MOONS={'Bellona','Gantz','Iktomia','Illium','Krawbek','Phoebe','Weldcog'}
FORGE_CHAOS={'Cavor Sarta','Crucible-Omega','Cyclothrathe','Diesos','Driantum','Forge Polix','Fortis Binary','Ironghast Foundry',"M'Pandex",'Quir','Samech','Silent Forge','Toil','Xana II'}
FORGE_LOC={'Agripinaa':('Obscurus','agripinaa'),'Antax':('Ultima','vidar'),'Demios Binary':('Obscurus','cadian'),'Duos':('Ultima','charadon'),'Ermune':('Pacificus',None),'Forge Polix':('Obscurus','calixis'),'Forge World Thule':('Tempestus','caligari'),'Fortis Binary':('Pacificus',None),'Gantz':('Ultima','ultima'),'Goth':('Obscurus','gothic'),'Hadd':('Obscurus','calixis'),'Haddrack':('Obscurus','calixis'),'Hervara':('Obscurus','calixis'),'Hesh':('Obscurus','calixis'),'Het':('Obscurus','calixis'),'Hypnoth':('Ultima','vidar'),'Idumea':('Obscurus','calixis'),'Iridial':('Ultima','traxis'),'JXM A18Z':('Obscurus','calixis'),'Kernak III':('Ultima','octarius'),'Kiavahr':('Tempestus','forsarr'),'Konor':('Ultima','ultima'),"M'Pandex":('Obscurus','gothic'),'Mezoa':('Obscurus','gothic'),'Lentrel Prime':('Ultima','vidar'),'Galatia':('Ultima',None)}
for name in FORGE:
 kind='moon' if name in FORGE_MOONS else 'planet'
 aff='Dark Mechanicum / Chaos' if name in FORGE_CHAOS else 'Adeptus Mechanicus historically; present allegiance not necessarily verified'
 seg,sid=FORGE_LOC.get(name,(None,None))
 note='Indexed forge moon rather than planet.' if kind=='moon' else 'Named in known forge-world index; individual conditions, allegiance and era require verification.'
 if name in FORGE_CHAOS:note+=' Chaos/Dark Mechanicum association stated in index.'
 if name in {'Hypnoth','Kernak III','Halfus'}:note+=' Source describes a later loss/conquest; older and newer affiliations differ.'
 if name=='Hekateus IV':note+=' Also listed as a Necron tomb world, Qivroth.'
 w=add(name,'Forge World' if kind=='planet' else 'Forge Moon',kind,aff,F,note,seg,sid)
 if name=='Hekateus IV':w.setdefault('aliases',[]).append('Qivroth')
 if name=='Glenescrede Raptus':w['era_status']['post_rift']='Exploded during the Thirteenth Black Crusade (check chronology).'
 # Important: a world-type designation is not sufficient to assert that a particular world has polluted air
# Index sometimes lists an old name of an already recorded world: preserve as separate until identity is verified.

ORK='''Absteron|Alacanth|Badlanding|Berin|Bork|Castellax|Charadon|Chosin|Cilix|Derragon|Dregrokk|Atari Vo's|Calverna|Emiline's Hope|Excovar|Eyrok|Flyberia|Garaghak's World|Golgotha|Gurgit's Mekworld|Imbrium|Keltor|Kongajaro|Krosk|Lethe Eleven|Magdelene IX|Mekslag-Ikks|Minos V|Moredakka|Obetrus|Ogrolla|Orrok|Periliac Prime|Perseus IV|Proctus Prime|Pseudopol|Redwold|Scalex VI|Scythia|Squire's Rest|Tallarax|Thoria III|Tigrus|Tyr|Ulani IV|Ulants|Krakskull|Snagruz|Stompgit|Tusk|Vorsk|Wrekker's World|Yurk|Zag|Zogg-Dis|Baran|Corinth|Dulma'lin|Ghorala|Graegus|Jagga|Urk|Xit'''.split('|')
FORMER_ORK={'Derragon','Ghorala','Keltor','Orrok','Baran','Corinth',"Dulma'lin",'Graegus','Jagga','Urk','Xit'}
for name in ORK:
  note='Named in Ork Domains; local control subject to historical period.'
  if name in FORMER_ORK:note+=' Listed as a former Ork world.'
  if name in {'Derragon','Keltor','Orrok','Ghorala'}:note+=' Overrun by Hive Fleet Leviathan in the Octarius War.'
  w=add(name,'Ork World' if name not in FORMER_ORK else 'Former Ork World','planet','Orks (historical or contested)',O,note)
  if name=='Bork' and w['factsheet_completeness']=='index_only':w['aliases']=['Bhorc Prime (Imperial designation)']
  if name=='Tyr':w.setdefault('possible_name_collision_note','There may be multiple worlds named Tyr, including a Necron-linked planet. Do not equate identities solely by name.')

# A first pass of explicitly indexed Knight worlds. Both Imperial and renegade associations exist.
KNIGHT='''Aaega|Adrastapol|Alaric Prime|Argentor|Atar-Planitia|Aurous IV|Avalane VI|Avarris|Baroda|Ceamira|Chrysis'''.split('|')
for name in KNIGHT:add(name,'Knight World','planet','Knight Houses (allegiance unspecified)',K,
                         'Indexed Knight World; sworn House, atmosphere, conditions and era not yet verified.')

# Improve existing planet-index entries with null-ish location_kind while keeping uncertitude in index notes
for w in wlist:
 if not w.get('location_kind'):
  w['location_kind']='planet'
  w['planetary_body_confidence']='general planetary index only; inspect linked article if natural/synthetic body is ambiguous'
 # re-normalize only brand-new entries with 'Unknown' atmospheric labels so environmental filter works
 w.setdefault('indexed_attestations',[w['source_url']] if w.get('source_url') else [])
# Name collision detection: distinguish same-world differently spelled names from same exact type
possible_aliases=[{'a':'Gorkamorka','b':'Angelis','relation':'historical_alias_to_verify'},
 {'a':'Bork','b':'Bhorc Prime','relation':'Ork/Imperial naming'},
 {'a':'Mpandex','b':"M'Pandex",'relation':'potential spelling alias; verify'},
 {'a':'Belacane','b':'Belecane','relation':'possible spelling variant; verify'},
 {'a':'Mero','b':'Meros','relation':'conflicting edition spelling'},
 {'a':'Chto','b':'Ctho','relation':'conflicting edition spelling'},
 {'a':'Drohai','b':'Dorhai','relation':'conflicting edition spelling'},
 {'a':'Forge World Thule','b':'Thule','relation':'possibly same world; verify'}]
d['potential_duplicates_and_aliases']=possible_aliases
# Avoid asserting known planet coordinates from generic segmentum diagrams.
assert len({w['id'] for w in wlist})==len(wlist), 'Duplicate world IDs'
assert len({w['name'].casefold() for w in wlist})==len(wlist),'Duplicate names'
assert all(not w.get('coordinates_verified') or w.get('position') for w in wlist)
# all linkage resolves
bysector={s['id'] for s in sectors}
assert all(not w.get('sector_id') or w.get('sector_id') in bysector for w in wlist)
for nm,url,scope in [('Lexicanum Forge World index',F,'Forge worlds with historical ownership changes and moons'),('Lexicanum Craftworld index',C,'Mobile craftworlds and destroyed craftworlds'),('Lexicanum Ork Domains',O,'Ork-held worlds with era-dependent control'),('Lexicanum Knight Worlds',K,'Partial Knight House planet index')]:
 if not any(s['url']==url for s in d['sources']):d['sources'].append({'name':nm,'url':url,'scope':scope})
count=collections.Counter(w.get('factsheet_completeness') for w in wlist)
d['coverage'].update({'named_location_rows':len(wlist),'index_only_locations':count.get('index_only',0),'curated_partial_locations':count.get('curated_partial',0),'named_craftworld_records':sum(w['location_kind']=='craftworld' for w in wlist),'named_forge_worlds_or_moons':sum('Forge' in w['world_type'] for w in wlist),'named_ork_world_records':sum('Ork World' in w['world_type'] for w in wlist),'source_verified_atmospheres':0})
d['version']='0.6-faction-world-index-expansion-2026-10-12'
d['research_method']='Manually transcribed selected named entries and limited classifications from public Lexicanum indexes; not a full scrape and not fully cross-checked against primary sources.'
d['source_specific_limitations'].extend(['Name-only additions from faction indexes do not establish a planet environmental profile','Craftworlds are mobile, artificial habitats and must not be plotted as fixed natural planets','A planet may have been an Imperial forge world and later an Ork or Chaos world; names need date-specific ownership','Similar names may denote the same planet; a potential alias audit is included'])
# Faction homeworlds extra data table with known cases, fact of no unique shared homeworld noted.
faction_homes=[
 {'faction':'Imperium of Man','main_world':'Terra','body_kind':'planet','notes':'Human cradle and Imperial capital.','status':'confirmed','source_url':'https://wh40k.lexicanum.com/wiki/Terra'},
 {'faction':'Adeptus Mechanicus','main_world':'Mars','body_kind':'planet','notes':'Primary cult/administrative center; not sole forge world.','status':'confirmed','source_url':'https://wh40k.lexicanum.com/wiki/Mars'},
 {'faction':'T’au Empire','main_world':'T’au','body_kind':'planet','notes':'Species origin; sept names are not all individual planet names.','status':'confirmed','source_url':'https://wh40k.lexicanum.com/wiki/T%27au'},
 {'faction':'Kroot','main_world':'Pech','body_kind':'planet','notes':'Kroot homeworld.','status':'confirmed','source_url':'https://wh40k.lexicanum.com/wiki/Pech'},
 {'faction':'Vespid','main_world':'Vespid','body_kind':'planet','notes':'Vespid origin world.','status':'confirmed','source_url':'https://wh40k.lexicanum.com/wiki/Vespid_(Planet)'},
 {'faction':'Necrons','main_world':'Multiple crownworlds/tomb worlds','body_kind':'distributed','notes':'Dynastic territories and crownworlds; no single modern civilization-wide capital planet.','status':'distributed','source_url':'https://wh40k.lexicanum.com/wiki/Tomb_World'},
 {'faction':'Aeldari Craftworlds','main_world':'No single current world','body_kind':'craftworlds','notes':'Distinct mobile craftworld societies; extinct ancient homeworlds not equivalent to one faction homeworld.','status':'distributed','source_url':C},
 {'faction':'Drukhari','main_world':'Commorragh','body_kind':'Webway city','notes':'Primary city in Webway; not a natural planet.','status':'confirmed','source_url':'https://wh40k.lexicanum.com/wiki/Commorragh'},
 {'faction':'Orks','main_world':'No single homeworld','body_kind':'distributed','notes':'Numerous Ork realms spread across the galaxy; Ullanor historically important.','status':'distributed','source_url':O},
 {'faction':'Leagues of Votann','main_world':'Galactic Core / numerous Holds','body_kind':'distributed','notes':'Numerous Kindreds and Holds; not one uniquely established capital world.','status':'distributed','source_url':'https://wh40k.lexicanum.com/wiki/Leagues_of_Votann'},
 {'faction':'Tyranids','main_world':'Unidentified extragalactic origin','body_kind':'unknown','notes':'Origin outside Milky Way unknown; hive fleets do not share a known galactic homeworld.','status':'unknown','source_url':'https://wh40k.lexicanum.com/wiki/Tyranid'},
 {'faction':'Chaos Space Marines','main_world':'Several Legion origins and daemon worlds','body_kind':'distributed','notes':'Legion-specific origins; Daemon Worlds may lack stable physical coordinates.','status':'distributed','source_url':'https://wh40k.lexicanum.com/wiki/Daemon_World'},
]
d['faction_homeworlds']=faction_homes
# Source audit
cols=collections.Counter()
audit=[]
for w in wlist:
  a=w['atmosphere'];s=w['surface']
  audit.append({'name':w['name'],'location_kind':w['location_kind'],'source':w['source_url'],'index_source':w.get('source_list_url') or '',
    'type':w['world_type'],'sector_id':w['sector_id'] or '', 'segmentum':w['segmentum'] or '',
    'review_state':w['review_state'],'factsheet_completeness':w['factsheet_completeness'],
    'atmosphere_known':not a.lower().startswith(('unknown','unspecified','not consistently','enclosed artificial')),
    'surface_known':not s.lower().startswith(('unknown','unspecified','artificial habitat')),
    'coordinates_known':w.get('coordinates_verified',False),'eye_relation':w['eye_relation'],
    'rift_side':w['rift_side'], 'indexed_attestations':' ; '.join(w.get('indexed_attestations',[]))})

def csvout(name,rows):
  fields=list(dict.fromkeys(k for row in rows for k in row))
  with (R/name).open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
    for row in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})
(R/'atlas_data.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
for nm,rows in [('locations.csv',wlist),('sectors.csv',sectors),('subsectors.csv',subs),('systems.csv',systems),('source_audit.csv',audit),('faction_homeworlds.csv',faction_homes),('possible_aliases.csv',possible_aliases)]:csvout(nm,rows)
# Inlined local browser app. Fixed a misleading visual copy inherited from starter prototype.
template=(R/'atlas_template.html').read_text('utf8')
template=template.replace('an offline, curated starter catalog','an offline, expanded but incomplete lore index')
template=template.replace('This is an offline, curated starter catalog.', 'This is an offline, expanded but incomplete lore index.')
template=template.replace('The central graphic is a','The central graphic is a')
template=template.replace('const kindLabel={planet:',"const kindLabel={artificial_habitat:'Artificial habitat',planet:")
# Generic 'atmosphere described' filter should not mistake explicit Unknown for described.
template=template.replace("/^(Unspecified\\.?|Not consistently)/i.test(w.atmosphere)","/^(Unspecified\\.?|Not consistently|Unknown|Enclosed artificial habitats)/i.test(w.atmosphere)")
app=template.replace('__ATLAS_JSON__',json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
(R/'atlas.html').write_text(app,'utf8')
readme=(R/'README.md').read_text('utf8')
readme=re.sub(r'\*\*\d+\*\* unique named planet, moon, habitat and other location records',f'**{len(wlist)}** unique named planet, moon, habitat and other location records',readme)
readme=re.sub(r'\*\*\d+\*\* additional `index_only` location records with skeletal factsheets; \*\*\d+\*\* edited seed factsheets',f'**{count.get("index_only",0)}** additional `index_only` location records with skeletal factsheets; **{count.get("curated_partial",0)}** edited seed factsheets',readme)
readme=readme.replace('- `tau_sept_systems.csv`:', '- `faction_homeworlds.csv`: distinguishes true central planets, distributed homeworlds, and nonplanet capitals.\n- `possible_aliases.csv`: unresolved suspected duplicate world and edition-spelling pairs.\n- `tau_sept_systems.csv`:')
readme+='\n## Third pass: faction indexes\n\nResearch added the [Forge World index]('+F+'), [Aeldari Craftworlds]('+C+'), and [Ork Domains]('+O+'), with a first sample from the [Knight World index]('+K+'). '+'Current total is **'+str(len(wlist))+'** individually named location rows including **'+str(sum(w['location_kind']=='craftworld' for w in wlist))+'** craftworlds.\n\nWorld classifications and names in these indexes were recorded without manufacturing planet-specific atmosphere or terrain descriptions. Some records in published indexes are moons or artificial habitats, while some same-name hits are historical alterations or independent names; see `possible_aliases.csv`. World count is *not* number of inhabited natural planets. Source index coverage is partial, primarily for planet list letters after the initial section.\n'
(R/'README.md').write_text(readme,'utf8')
path=Path('/mnt/data/warhammer40k_galactic_atlas_expanded.zip')
with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for nm in ['atlas.html','atlas_data.json','locations.csv','sectors.csv','subsectors.csv','systems.csv','source_audit.csv','faction_homeworlds.csv','possible_aliases.csv','tau_sept_systems.csv','primarch_homeworlds.csv','README.md','atlas_template.html','enrich_research.py','enrich_factions.py','build.py']:
  z.write(R/nm,arcname='warhammer40k_atlas/'+nm)
print(json.dumps({'locations':len(wlist),'sectors':len(sectors),'subsectors':len(subs),'systems':len(systems),'new_faction_counts':dict(counts),'craftworlds':sum(w['location_kind']=='craftworld' for w in wlist),'forge':sum('Forge' in w['world_type'] for w in wlist),'zip_size':path.stat().st_size},indent=2))
