"""Second-pass atlas enrichment from indexed sources checked 2026-10-12.
Deliberately preserves unknowns; sourced INDEX rows are not fully researched factsheets.
"""
import csv,json,re,collections,zipfile,io
from pathlib import Path
from urllib.parse import quote
R=Path('/mnt/data/warhammer40k_atlas')
d=json.loads((R/'atlas_data.json').read_text(encoding='utf8'))
S='https://wh40k.lexicanum.com/wiki/List_of_sectors'
P='https://wh40k.lexicanum.com/wiki/List_of_planets'
T='https://wh40k.lexicanum.com/wiki/Tomb_World'
CAL='https://wh40k.lexicanum.com/wiki/Planets_of_the_Calixis_Sector'
sectors=d['sectors']; locations=d['locations']; subsectors=d['subsectors']; systems=d['systems']
slug=lambda n:re.sub('[^a-z0-9]+','-',n.lower()).strip('-')
# All additional sector-like entries were transcribed from the distinct TOP-LEVEL rows of Lexicanum's sector list.
# No fabricated geography. 'Eastern Fringe' is NOT a sixth segmentum.
SECTOR_ADD='''
Asmodiox|Pacificus|sector
Athelaq||sector
Athena||sector
Bakhar|Ultima|sector
Barbarus|Tempestus|sector
Bastion||sector
Bethesba||sector
Boras Minor|Ultima|sector
Borodance||sector
Chonma|Solar|sector
Cirillo|Ultima|sector
Coronid Deeps||region
Corribra|Tempestus|sector
Crucis||sector
Demeter|Ultima|sector
Finial|Obscurus|sector
Fordan||sector
Formosa|Ultima|sector
Forsarr|Tempestus|sector
Fourth Quadrant|Solar|sector
Gerio||sector
Gilead|Ultima|sector
Goliant||sector
Gorath|Ultima|sector
Grimmok||sector
Gulgorahd Protectorate|Ultima|region
Herakon Cluster||cluster
Loki|Ultima|sector
Macharian|Pacificus|sector
Macharius Alpha|Pacificus|sector
Machorta|Pacificus|sector
Magog Cluster|Ultima|cluster
Magulanox||sector
Malagant||sector
Mandragora||sector
Mitre Gulf||region
Momed||sector
Morpheum|Pacificus|sector
Nachmund|Obscurus|sector
Narasima|Obscurus|sector
Nemesys|Tempestus|sector
Nepthis||sector
Nostramo|Ultima|sector
Octarius|Ultima|sector
Opal||sector
Oqueth||sector
Orpheus|Tempestus|sector
Pyrus Reach||region
Sabbat Worlds|Pacificus|region
Sadusyne||sector
Sangramentia||sector
Saras||sector
Sargos||sector
Scaephan|Tempestus|sector
Scarla|Tempestus|sector
Scyllan|Obscurus|sector
Sexton|Ultima|sector
Shadefrost||sector
Spartus|Tempestus|sector
Stygius||sector
Taebian|Ultima|sector
Talis Munus|Solar|sector
Tamahl|Obscurus|sector
Tertius|Solar|sector
Thramas|Ultima|sector
Trail of Saint Evisser|Solar|region
Traxis|Ultima|sector
Uhulis|Tempestus|sector
Ulik|Ultima|sector
Ullanor||sector
Upsilon-Xi|Ultima|sector
Urdonne||sector
Vandreggan||sector
Veldin||sector
Veneros||sector
Vensine||sector
Vertex||sector
Viceroy|Ultima|sector
Vordral||sector
Vynor|Pacificus|sector
Yasan|Ultima|sector
Zeist|Ultima|sector
'''.strip()
bysec={s['id']:s for s in sectors}
for line in SECTOR_ADD.splitlines():
 name,seg,kind=line.split('|');ident=slug(name)
 if ident not in bysec:
  o={'id':ident,'name':name,'segmentum':seg or None,'category':kind,'source':S,'confidence':'index_only','map_coordinates':None,'review_state':'secondary_index_only'}
  sectors.append(o);bysec[ident]=o
# Source-confirmed fixes, preserving notes for any cross-segmentum distinctions.
for name,seg in [('Medusan','Obscurus'),('Barbarus','Tempestus')]:
 if slug(name) not in bysec:
  o={'id':slug(name),'name':name,'segmentum':seg,'category':'sector','source':S,'confidence':'index_only','map_coordinates':None};sectors.append(o);bysec[o['id']]=o
bysec['stygius']['segmentum_note']='Described as spanning the Obscurus/Ultima border; no single segmentum enforced.'
for s in sectors:
 s.setdefault('review_state','secondary_index_only')
 s.setdefault('source_list_url',S)
 s.setdefault('sector_geometry','unknown')
 s.setdefault('coordinates_verified',False)
 if s['category'] in ('cluster','region','disputed_sector_or_subsector'):
  s.setdefault('boundary_note','Distinct regional designation; should not be forced into the same spatial type as a sector.')
# Securing the source-defined hierarchy without claiming every nominal reach is administratively a subsector.
SUBS='''
Armageddon|Desedna & Paleoth
Armageddon|Golgotha
Armageddon|Justicar
Armageddon|Voss Prime
Askellon|Asphodel Depths
Askellon|Cyclopia
Askellon|Rubicon
Askellon|Stygies Cluster
Askellon|Thule
Asmodiox|Byroth
Asmodiox|Polidara
Asmodiox|Shaele
Barbarus|Urphir
Bethesba|Pontic
Bethesba|Segesta
Boras Minor|Therion
Caligari|Tenebra
Calixis|Spinward Front
Charadon|Anungul
Charadon|Charus
Charadon|Lirac
Charadon|Palan
Charadon|Phlegyr
Charadon|Psyphos
Charadon|Urshan
Chiros|Agritha
Chiros|Kalidar
Coronid Deeps|Coronid Reach
Coronid Deeps|Cyclops Cluster
Coronid Deeps|Grail Abyss
Forsarr|Kastorel-Severus
Fourth Quadrant|Sulsalid
Gothic|Bhein Morr
Gothic|Cyclops Cluster
Gothic|Gethsemane
Gothic|Lysades
Gothic|Orar
Gothic|Port Maw
Gothic|Quinrox Sound
Lithesh|Timbra
Loki|Hebrides
Macharius Alpha|Caracros
Nachmund|Gorandahl
Nachmund|Nachmund
Nachmund|Vigilus
Nostramo|Nostramo
Octarius|Talaveris
Orpheus|Capitoline
Orpheus|Deluvian
Orpheus|Drucillan
Red Scar|Cryptus
Red Scar|Vitria
Sabbat Worlds|Cabal Systems
Sabbat Worlds|Carcaradon Cluster
Sabbat Worlds|Erinyes Group
Sabbat Worlds|Khan Group
Sabbat Worlds|Newfound Trailing Group
Sabbat Worlds|Nubila Reach
Scaephan|Obsidian
Scarla|Scarla Trigate
Scarus|Antimar
Scarus|Angelus
Scarus|Helican
Scarus|Kerak
Scarus|Ophidian
Scarus|Vincies
Scyllan|Atreyan
Stygius|Dhobash
Stygius|Khravos
Stygius|Mordian
Stygius|Prismata
Stygius|Salamar
Stygius|Urtek
Talis Munus|Caerulus-Primaris
Tertius|Veritus
Thramas|Aegis
Ultima|Ultramar
Viceroy|Niaides
Vidar|Ironhame
Vidar|Zorya
Yasan|Chogoris
'''.strip()
subids={x['id'] for x in subsectors}
for line in SUBS.splitlines():
 sec,name=line.split('|');secid=slug(sec);ident=slug(sec+'-'+name)
 if ident not in subids and secid in bysec:
  subsectors.append({'id':ident,'name':name,'sector_id':secid,'source_url':S,'category':'subsector_or_named_subregion','membership_confidence':'listed','source_field':'Subsectors'});subids.add(ident)
# Independently listed subsector names lacking a known parent are retained explicitly.
SUB_INDEPENDENT='''
Achilles|Obscurus
Agartha|
Andosk|
Avalonia|
Bastior|
Belial IV|
Caliban|
Orco-Pelica|Ultima
Orlanni|
Pankallis|Ultima
Perditha|Ultima
Prath Veil|Obscurus
Proxima Sol-Tertius|Solar
Ras|
Sagan|Ultima
Sanctus|Ultima
Scelus|Obscurus
Soelich|Tempestus
Thirsis|Ultima
Titus|
Verlax Tertius|
Vorsk|
Wessago|
Wheel of Fire|Ultima
Xibana Reaches|
Yossarian|
Zypher|
'''.strip()
for line in SUB_INDEPENDENT.splitlines():
 n,seg=line.split('|');ident='unassigned-'+slug(n)
 if ident not in subids:
  subsectors.append({'id':ident,'name':n,'sector_id':None,'segmentum':seg or None,'source_url':S,'category':'unassigned_subsector_or_reach','membership_confidence':'unknown','source_field':'Unstated'});subids.add(ident)
for r in subsectors:r.setdefault('review_state','secondary_index_only')
# Surface descriptions based strictly on the lexical world-type (no invented gases, temperatures, flora or chemistry).
def indexed_surface(world_type):
 t=world_type.lower()
 for key,val in [
 ('ocean','Ocean-dominated terrain (world-classification inference only).'),
 ('desert','Desert terrain (world-classification inference only).'),
 ('jungle','Jungle-covered terrain (world-classification inference only).'),
 ('forest','Forested terrain (world-classification inference only).'),
 ('ice world','Icy terrain (world-classification inference only).'),
 ('molten','Molten surface (world-classification inference only).'),
 ('hive','Hive city complexes; extent and terrain not independently documented.'),
 ('forge','Industrial/forge complexes; extent and terrain not independently documented.'),
 ('mining','Resource extraction sites; terrain unverified.'),
 ('agri','Agricultural production; topography unverified.'),
 ('tomb','Necron tomb structures may be present; specific surface unverified.')]:
  if key in t: return val
 return 'Unknown; not documented in reviewed index.'
for w in locations:
 w.setdefault('source_list_url',None)
 w.setdefault('environment_evidence','curated_seed_secondary_link')
 w.setdefault('coordinates_verified',False)
 w.setdefault('planet_position_source',None)
 w.setdefault('time_scope','varies_by_source')
 w.setdefault('factsheet_completeness','curated_partial')
byworld={w['name'].casefold():w for w in locations}
# Compact verified-index transcription. Format: name | world type | segmentum | sector | factual note | faction | kind
# Source = the Lexicanum world list unless overridden. Additional named worlds from the sector index below.
WORLDS='''
108/Beta-Kalapus-9.2|Adeptus Astartes Homeworld|||Home of Wolfspear Space Marines|Imperium|
42 Hydra Tertius|Unclassified|||Also known as Eolith||
8-Rho-krame|Former Armoury World|||Abandoned, overtaken by Orks|Orks|
Abandoned Hope|Forbidden World|Obscurus|Calixis|Josian Reach; access restricted|Imperium|
Abheilüng|Forge World|Solar||Dark Mechanicum forges|Chaos / Dark Mechanicum|
Abramis VII|Unclassified|||||
Absolom Reach|Daemon World; former Hive World; former Desert World||||Chaos|
Accatran|Forge World|Ultima|||Adeptus Mechanicus|
Acheron IV|War World; Forge World|||||
Acanon|Homeworld|Solar||Emperor's Blades death cult||
Acralem|Unclassified|Ultima||Daemonic incursion in 799.M41||
Actium|Jungle World|||||
Adacore|Mining World||||Imperium|
Adrantis Five|Dead World|Pacificus||||
Adric IV|Unclassified|||Ecclesiarchal hermitage attacked by Necrons||
Adumbria|Civilised World|||Tidally locked with desert hemisphere and ice hemisphere|Imperium|
Adun|Shadow World|||||
Ae|Forest World|||||
Aerius|Hive World|||||
Aeteria|Unclassified||Oqueth|Oqueth Sector world||
Aggaros|Feral World|Obscurus||||
Aggenon|Former Shrine World|||Invaded by Aeldari in M41||
Aggreon|Unclassified|||||
Aghoru|Unclassified|||||
Agraria XIII|Unclassified|||||
Agripinaa|Forge World|Obscurus|Agripinaa||Adeptus Mechanicus|
Agrippus|Prison World|Ultima||Attila System|Imperium|
Akandat|Death World|Obscurus||Dhobash System||
Aipolodon IV|Agri World|||||
Alactra|Hive World|Obscurus|Calixis|Malfian Subsector|Imperium|
Alantor X|Unclassified|||Destruction of Angels of Retribution||
Alsor|Unclassified|Obscurus|Scarus|Helican Subsector||
Alayran|Maiden World||||Aeldari|
Albert IV|Forge World||||Adeptus Mechanicus|
Albitern|Unclassified|Obscurus||Howling Griffons fought daemons||
Alcatran|Hive World|||||
Aldarast|Unclassified|||||
Alena-Mora|Unclassified|||Homeworld of Inquisitor Ivixia Dannica||
Alexandrum|Archivum World|Ultima||Attila System||
Alexandrus|Feudal World|||||
Alfrost|Death World|Ultima||Space Wolves fought in the Crusade of Fire||
Algol|Hive World|||||
Algol Nine|Unclassified|||||
Almarit|Daemon World; former Fortress/Shrine World||||Chaos|
Alpha Shalish|Dead World|Solar||||
Alphex|Unclassified|||||
Altair VII|Unclassified|||||
Altaneum|Ocean World|||||
Arcadia|Xenos World|||Holds ancient Harlequin libraries|Aeldari|
Arcadia Secundus|Unclassified|||||
Arcetri|Dead World; former Forge World|||Consumed by Hive Fleet Harbinger|Tyranids|
Archaos|Hive World|Obscurus||||
Archangelsk|Dead World; former Gas Giant|||Destroyed 319.M36||
Archipelaga|Feral World; Ocean World|Ultima||Reclaimed after Damocles Gulf Crusade||
Archona|Hive World|Ultima||||
Archos|Unclassified|||||
Arconar|Feral World|||||
Ardenz IV|Unclassified|||||
Areadnnil|Exodite World|Ultima|||Aeldari|
Argentor|Knight World|Obscurus||Imperial Knight house presence|Imperium|
Argonan|Unclassified|Tempestus||||
Argo Secundus|Unclassified|||||
Arimaspia|Industrial World|Obscurus||Orbited by Chrysalis Shipyards||
Ariyo|Unclassified|||Dekradek System||
Ark Reach Secundus|Dead World|||Former Imperial world||
Arkadia|Unclassified|||||
Arkalli|Industrial World|||Industrial center at reach of Astronomican||
Arkhona|Dead World|Obscurus|Scyllan|Site of Eternal Crusade||
Arkost|War World; Shrine World|||||
Arkunasha|Desert World; Xenos World|Ultima||T'au Empire colony|T'au Empire|
Armato|Adeptus Astartes Homeworld|Ultima||Home of Sons of Orar|Imperium|
Arminiun|Imperial World|||Home of Honus Squad|Imperium|
Artemia Majoris|Forge World|Pacificus||Site of Hieronymite Heresy|Adeptus Mechanicus|
Arthas|Unclassified|||Conquered by Death Guard|Chaos / Death Guard|
Arthas Moloch|Dead World; Artefact World|Ultima||Dawn Blade was found here||
Arthos|Unclassified|||||
Avalus|Unclassified|||Central world of Lion's Protectorate||
Aryand|Hive / Tomb World|||Nephrekh Necrons occupied formerly Imperial hive|Necrons / Nephrekh|
Aryus Onc|Feudal World|Obscurus|Calixis|Malfian Subsector||
Arx|Research Station|Obscurus||Route out of Eye of Terror||
Asgard|Feudal World|||Asgardian Rangers founding world|Imperium|
Ashek II|Hive World|Pacificus||Sabbat Worlds Crusade reconquered|Imperium|
Ashen|Cemetery World|Obscurus|Calixis|Spinward Front; Periphery|Imperium|
Asinia|Shrine World|Ultima|Cirillo|Golden Chain||
Askelphion Secundus|Paradise World|Obscurus|Calixis|Drusus Marches|Imperium|
Asmordean V|War World|||||
Aspen II|Civilised World|Ultima||||
Asphodel|Swamp World|Obscurus||Screaming Vortex Kroot world|Kroot|
Asterion|Hive World|Obscurus|Calixis|Spinward Front; Periphery||
Asur|Xenos World|||First Aspect Warrior shrine|Aeldari|
Atalia Minoris|War World|||||
Atari Vo|Ork World; former T'au Sept World|Ultima||Currently Ork held|Orks|
Aten III|Industrial World|Obscurus||||
Athanos|Unclassified|Tempestus||||
Athonos|Civilised World; former Tomb World|Tempestus||Home of Athonian Tunnel Rats|Imperium|
Atoma Prime|Hive World|Solar||Capital of Moebian Domain|Imperium|
Atraxian III|Unclassified|Obscurus|Calixis|||
Attila|Feudal World|Ultima||||
Augura|Imperial World; former T'au World|Ultima|Zeist||Imperium|
Augury|Daemon World|Obscurus|Calixis|The Periphery; Spinward Front|Chaos|
Aumet|Imperial World|Obscurus|||Imperium|
Aurelia|Former Astartes Homeworld|Ultima|Korianis|Original Blood Ravens homeworld; lost in M40/M41|Imperium|
Auric|Unclassified|Tempestus||||
Avarax|Hive World|Pacificus||Tyranid invasion in M42||
Avellorn|Civilised World|Obscurus|Askellon||Imperium|
Aventine|Civilised World|Solar||Iron Warriors attack during Heresy|Imperium|
Avignor|Cardinal World|Obscurus||||
Avitohol|Agri World; Xenos World|Obscurus|Calixis|Periphery; disputed Imperial/Ork|Imperium / Orks|
Azazen|Frontier World|Solar||||
Azbaragus|Nurgle World||||Chaos|
B8400761|Artificial World; War World|Ultima||||
Baalus Trine|Feral World|||Recruiting world for Angels Sanguine|Imperium|
Badsquig|Feral World|Ultima||Octarius System|Orks|
Baedros|Shrine World|||||
Baih'Rus|Colony World|||Eastern Fringe||
Bakka|Forge World; Segmentum Fortress|Tempestus||Tempestus fleet headquarters|Imperium / Adeptus Mechanicus|
Bakus III|Hive World|||||
Balcarhsa|Unclassified|Ultima||||
Balecaster|Feudal World|Obscurus|Calixis|Markayn Marches|Imperium|
Balhaut|Cemetery World|Pacificus||Sabbat Worlds Crusade battleground|Imperium|
Balle Prime|War World|Pacificus||||
Balor|Mining/Ocean World|Ultima||Balor System||
Balzac|Mining World|Obscurus||||
Banish|Astartes Homeworld|Obscurus|Narasima|Exorcists chapter homeworld|Imperium|
Banna|Civilised World|Solar||||
Baran|Former Exodite World|||Currently Imperial held|Imperium / Aeldari (historical)|
Bararat|Former Xenos World|||||
Barbarus Prime|Dead World; former Mining World|Ultima||||
Baroda|Knight World|Obscurus||Formerly home to House Makabius|Imperium (former)|
Baryatin II|Unclassified|Pacificus||||
Bastion|Dead World|||||
Bastonbeil|Daemon World; former Hive World|Ultima||Enslaved by Company of the Shadow|Chaos|
Beati Sedna|Shrine World|||||
Bekrin|Dead World; former Shrine World|Ultima||Destroyed by Hive Fleet Dagon||
Belaeno|Jungle World|||||
Belahaam|Forbidden World; Xenos World|Obscurus|Calixis|Hazeroth Subsector||
Belatis IV|Shrine / Ice World|||||
Belecane|Forge World|Obscurus|Calixis|Markayn Marches|Adeptus Mechanicus|
Belial|Hive / Industrial World|||||
Cadamine|War / Forge World|||||
Cagalian IX|Mining World|Obscurus||Genestealer cult takeover|Genestealer Cult|
Cadmus Phosp|Unclassified|||||
Caer Malafori|Unclassified|||||
Cyrus Vulpa|Agri World|Obscurus|Calixis|Drusus Marches|Imperium|
Cytheria|Xenos/Jungle World|Ultima||Captured by T'au from Imperium|T'au Empire|
Dabenlar IV|Unclassified|||||
Daedallos|Unclassified|Ultima||||
Daea|Death World|Tempestus||Consumed by Tyranids|Tyranids|
Daemos III|Unclassified|||||
Dakaram|Death World|||||
D'akhar|Death / Desert / Industrial World|||||
Dakidda|Fortress World|Obscurus||Dhobash System||
Dakkazot|Ork War World|Ultima||Octarius System|Orks|
Dalos Prime|Unclassified|||||
Dwimlicht|Feral World|Obscurus|Calixis|Hazeroth Subsector||
D'yanoi|T'au Sept World|Ultima|||T'au Empire|
Dynax-Abultra|Forge World|||Near Ullanor System||
Dynax Primus|Forge World|||||
Dynostix V|Forge World|||||
Ecovoria|Forge World|||||
Ector|Hive World|Tempestus||Consumed by Tyranids||
Ectosa|Unclassified|Obscurus||||
Eden Prime|Former Agri World|||Destroyed late M41||
Fulgor II|War/Industrial World|||||
Furund|Ice World|||||
Furia|Ocean World|Obscurus||Screaming Vortex||
Fydae Minos|Agri World|Obscurus|Calixis|Malfian Subsector||
Gabrydon|Mining World|||||
Gacrux|Desert World|||||
Galaspar|Hive World|||||
Galathas II|Ice World|||||
Galavan|Jungle World|||||
Galen VI|Frontier World|||||
Galfranus V|Agri World|||||
Maccabeus Quintus|Shrine World|Obscurus|Calixis|Drusus Marches||
Machiun|Unclassified|Ultima||Arbites training world||
Malodrax|Former Fortress World|||Destroyed by Exterminatus 971.M41||
Malvolion|Dead World; former Agri World|||Consumed by Tyranids||
Mancora|Astartes Homeworld; Feudal/Knight World|Ultima||Howling Griffons homeworld|Imperium|
Manus Cenita|Hive World|Obscurus|Calixis|The Periphery; Spinward Front||
Manzipor|Civilised World|Ultima||||
Outrenacht|Astartes Homeworld|Obscurus||Legion of Night homeworld|Imperium|
Oxatan|Astartes Homeworld|Ultima||Red Legion homeworld|Imperium|
Palatine III|War / Forge / Ork World||||Orks|
Palaxion II|Shrine World|||Daemonic invasion defeated by Grey Knights||
Palinurus Rhys|Frontier World|Obscurus|Calixis|Josian Reach||
Palis II|Dead World|||||
Palomar|Dead World; former Forge World|||||
Pyrites|Civilised World|Pacificus||||
Pyrrhia|Tomb World||||Necrons|
Quanta Magnifica|War World|||||
Quatara-Prime|Desert World|||||
Quatra|Desert World|||||
Quintarn|Agri/Desert World|Ultima|Ultima|One of nine worlds of Ultramar|Imperium|
Quatro|Unclassified|||||
Sycorax|Death World|Ultima||||
Symeon|Heretic Astartes Recruiting World||||Chaos|
Synford|Forge World|Obscurus|Calixis|Hazeroth Subsector||
Synford II|Forge World|Obscurus|Calixis|Malfian Subsector||
T'ruen|T'au World|||Attacked by Hive Fleet Eumenides|T'au Empire|
Tabor|Hive/Ocean World|Obscurus|Agripinaa||Imperium|
Taeloth|Uninhabited World|Obscurus||||
Tahnel|Civilised/Ocean World|Solar||||
'''.strip()

# Add targeted planets named by sector index, including worlds that would otherwise be unsearchable by sector.
# Uses S as provenance; sector membership is literal from the indexed sector table.
SECTOR_WORLDS='''
Abiaus|Piscina IV
Adraphane|Enth
Armageddon|Voss Prime;St Jowen's Dock
Asmodiox|
Bakhar|Bakhar Prime;Zanzamon
Barbarus|Beta Anphelion IV
Bethesba|Pontus;Emcor
Calaphrax Cluster|Exyrion;Pandrosar;Tintaroth
Chelio|Roxanzand
Chiros|Geratomro;Kalidar IV
Chonma|Hermetica
Corribra|Asperity
Crucis|Laius Rift
Demeter|Pythos
Donian|Nickel V
Donorian|Donoria Prime
Ephialtis|Ceocan
Fenris|Midgardia
Formosa|Epsilon Regalis;Glovoda;Promulgatia
Forsarr|Kastorel;Garaghak's World;Mekslag-Ikks
Fourth Quadrant|Lycanthos Secundus
Gerio|Archus
Gorath|Siluria IV
Gulgorahd Protectorate|Gulgorahd;Memlock
Helioret|Luxor
Hodur|Talon;Endragiga
Ixaniad|Scoth
Karthago|Sidon Ultra
Lithesh|Kronus;Kaurava III
Loki|Rynn's World;Badlanding
Macharius Alpha|Istrouma
Magulanox|Cernis IV;Quintus
Mitre Gulf|Burjan's World
Nachmund|Vigilus;Dharrovar;Sangua Terra
Narasima|Banish
Nemesys|Bheta-Decima
Nostramo|Occludus
Orpheus|Libethra;Saint Marduk's Bane
Palatine|Eurytion;Sanctus Lys
Pegasus|Hymir II
Priam|Darkstation
Red Scar|Satys
Reductus|Stratos
Sabbat Worlds|Formal Prime
Sangramentia|Dennar IV
Saras|Saras VII
Scaephan|Proxiphan;Infernis Magna;Vanqualis;Voiderhome;Tyrancos
Scyllan|Arkhona
Sexton|QX-937
Shadefrost|Shadefrost Prime
Stygius|Mordia
Talis Munus|Betalis III
Tertius|Benediction
Thramas|Desperation;Sheol;Tsagualsa
Trail of Saint Evisser|Trepytos
Uhulis|Krieg
Ullanor|New Mitama;Nalkari
Ultima|Calth;Talasa Prime;Talassar
Urdonne|Eleutane
Vandreggan|Euesa
Veneros|Phirus
Vensine|Kolagar
Vertex|Vertex
Viceroy|Maginor
Vidar|Carnac;Davatas;Hypnoth;Praedis Zeta;Prism;Safehold;Sanctuary 101;Schrödinger VII;Somonor
Yasan|Chogoris
Zeist|Praetonis V
'''.strip()

# Records copied from a dedicated Necron Tomb World *index*, each with source provenance.
NECRON='''
Akator|Tempestus||Necrons|Tomb World|
Akynatos|||Necrons / Sautekh|Tomb World|Infiltration defences
Ankekh|||Necrons|Tomb World|
Avarris|Ultima|Vidar|Imperium|Knight / Tomb World|
Bardic|Ultima||Necrons|Tomb World|
Bekyra|||Necrons|Tomb World|Awakened Council in M31
Bellicas|Ultima||Imperium|Astartes / Tomb World|Emperor's Swords homeworld
Berien|||Necrons|Dead / Tomb World|
Brogrod|Ultima||Necrons|Tomb World|
Cano'var|||Necrons / Sautekh|Tomb World|Former T'au world
Carnac|||Necrons|Former Exodite / Tomb World|
Carnotite|||Necrons|Tomb World|Living-brain world
Carrion Deep|Tempestus||Necrons|Dead / Tomb World|
Chandrax II|||Necrons|Tomb World|Former Imperium
Cocholos|||Chaos|Former Tomb World|Former Imperium and Necrons
Cthelmax|Ultima||Unspecified|Tomb World|
Davatas|Ultima|Vidar|Necrons / Sautekh|Tomb World|Sautekh coreworld
Demerium|Pacificus||Imperium|Cemetery / Tomb World|
Dhol VI|Ultima||Unspecified|Tomb World|
Doahht|||Necrons|Crownworld|Ghoul Stars; unknown dynasty
Draven|Ultima||Necrons / Novokh|Tomb World|
Fordris|||Necrons|Tomb World|
Gheden|Ultima||Necrons / Nihilakh|Crownworld|Nihilakh capital
Ghelleph|||Necrons|Tomb World|
Gidrim|Ultima||Necrons / Sautekh|Tomb World|
Hollow Sun|Ultima||Necrons / Suhbekhar|Crownworld|Suhbekhar dynasty capital
Icnarus|||Imperium|Former Tomb World|Reclaimed frontier world
Iori Delta Tove|||Necrons|Tomb World|
Interitus Prime|||Unknown|Tomb World|
Ixya|||Necrons|Tomb World|Former Imperial mining world
Kaurava III|Ultima|Lithesh|Imperium|Tomb World|
Kavardia|||Necrons / Oroskh|Tomb World|
Kinbriar|Obscurus||Necrons|Tomb World|
Kronus|Ultima|Lithesh|Imperium|Civilised / Tomb World|
Lorn V|||Imperium|Former Exodite / Tomb World|
Loxar IV|||Imperium|Industrial / Tomb World|
Luther Macintyre IX|Ultima||Imperium|Death / Tomb World|Tomb association possibly disputed
Maedrax|||Necrons|Tomb World|
Magistrakh|||Necrons / Technomandrites|Tomb World|
Medusa VII|Ultima||Necrons / Sautekh|Tomb World|
Meghoshta|Pacificus||Necrons / Thokt|Crownworld|Thokt dynasty capital
Moebius|Ultima||Necrons / Nekthyst|Tomb World|
Morrigar|||Necrons|Tomb World|Former Hive and Dead World
Morrigor|||Necrons|Tomb World|
Nagathar|Ultima||Necrons|Tomb World|
Naogeddon|||Necrons|Tomb World|
Nervkor|Pacificus||Necrons|Tomb World|
Nymidae|||Unknown|Tomb World|
Orrak|Ultima||Necrons / Hyrekh|Tomb World|
Pavonis|Ultima||Imperium|Mining / Tomb World|
Perdita|Ultima||Necrons / Mephrit|Tomb World|
Phaethon IV|||Necrons|Former Industrial / Tomb World|
Primordus IV|||Necrons / Xonthar|Former Industrial / Tomb World|
Pyrodiah|||Imperium|Tomb World|
Qyrakotosh|Ultima||Necrons / Mephrit|Tomb World|
Rithcarin|Ultima||Necrons / Sautekh|Tomb World|
Sanctarro|||Necrons|Tomb World|
Santos 9|||Necrons|Desert / Tomb World|
Sarkon|Obscurus||Necrons / Empire of the Severed|Tomb World|Empire of the Severed capital
Sarlok|Ultima||Necrons / Sekemtar|Crownworld|Sekemtar capital
Schrödinger VII|Ultima|Vidar|Necrons / Sautekh|Ice / Tomb World|Former Imperial Hive/Mining World
Seidon|Ultima||Necrons|Tomb World|Ancient Necrontyr heartland
Septimus Moore|Ultima||Necrons|Tomb World|
Shemnoch|||Unknown|Former Tomb World|Former Shemnoch Dynasty
Simia Orichalcae|||Imperium|Ice/Mining/Tomb World|
Somonor|Ultima|Vidar|Necrons / Sautekh|Tomb World|
Sovereign|||Necrons|Tomb World|
Suranas|||Necrons|Tomb World|
Tamar|Pacificus||Necrons / Ogdobekh|Tomb World|
Thridia|||Imperium|Hive / Tomb World|
Trakonn|Ultima||Necrons / Dyvanakh|Crownworld|Dyvanakh capital
Trantis|Tempestus||Necrons|Tomb World|Also named Raider's Moon; actual body type review needed
Trynnect|Solar||Necrons|Tomb World|
Tymatros Aleph|||Unknown|Tomb World|
Tyr|Tempestus||Necrons / Flayed Ones|Tomb World|
Uttu Prime|Ultima||Necrons / Sautekh|Tomb World|Former Imperial world
'''.strip()

def newworld(name,typ='Unclassified',seg='',sec='',note='',fac='',kind='planet',url=P,index='planets_list'):
 key=name.casefold()
 # avoid false name collision, especially sector = world names; no 'Ullanor' world duplication.
 if key=='ullanor':
  return None
 if key in byworld:
  w=byworld[key]
  w.setdefault('indexed_attestations',[])
  if url not in w['indexed_attestations']:w['indexed_attestations'].append(url)
  if sec and not w.get('sector_id') and slug(sec) in bysec: w['sector_id']=slug(sec)
  if seg and not w.get('segmentum'):w['segmentum']=seg
  return w
 secid=slug(sec) if sec and slug(sec) in bysec else None
 o={'id':slug(name),'name':name,'location_kind':kind,'segmentum':seg or None,'sector_id':secid,
    'world_type':typ or 'Unclassified', 'affiliation':fac or 'Unspecified',
    'surface':indexed_surface(typ),'atmosphere':'Unspecified; not documented in reviewed index.',
    'notable':note or 'Named in indexed lore; detailed environmental survey pending.',
    'source_url':url,'source_tier':'Lexicanum secondary index; original published source not checked',
    'source_list_url':url,'review_state':'index_only','eye_relation':'unknown','rift_side':'unknown','position':None,
    'era_status':{'pre_eye':'Unknown','pre_rift':'Unknown','post_rift':'Unknown'},'history':[],
    'system_id':None,'subsector_id':None,'factsheet_completeness':'index_only','environment_evidence':'world_type_inference_only' if indexed_surface(typ).startswith('Unknown') is False else 'unknown',
    'coordinates_verified':False,'planet_position_source':None,'time_scope':'unspecified','indexed_attestations':[url]}
 locations.append(o);byworld[key]=o;return o
for line in WORLDS.splitlines():
 fields=line.split('|'); assert len(fields)==7,(len(fields),line)
 newworld(*fields,url=P)
# Add sector index entries without making planetary worlds from stations/rifts.
NONPLANET={'St Jowen\'s Dock':'space_station','Laius Rift':'nonplanet','Darkstation':'space_station','Dharrovar':'nonplanet','Sangua Terra':'nonplanet'}
for line in SECTOR_WORLDS.splitlines():
 sec,names=line.split('|')
 if not names:continue
 for name in names.split(';'):
  if not name:continue
  if NONPLANET.get(name)=='nonplanet':continue
  seg=bysec.get(slug(sec),{}).get('segmentum') or ''
  typ='Unclassified';kind=NONPLANET.get(name,'planet')
  if name=='Rynn\'s World':typ='Astartes Homeworld'
  elif name=='Kronus':typ='Civilised / Tomb World'
  elif name=='Beta Anphelion IV':kind='moon'
  elif name=='Pythos':typ='Death World'
  elif name=='Krieg':typ='Death World'
  elif name=='Calth':typ='Cavern / War World'
  elif name=='Midgardia':typ='Imperial World'
  newworld(name,typ,seg,sec,'Recorded in sector index as notable location','',kind,S,'sectors_list')
for line in NECRON.splitlines():
 fields=line.split('|');assert len(fields)==6,fields
 name,seg,sec,fac,typ,note=fields
 newworld(name,typ,seg,sec,note,fac,'planet',T,'tomb_index')
# Additional checked Tau sept worlds from source index: don't conflate sept (star system) with proven planet if no planet is established.
TAU_SEPT_SYSTEMS=['D\'yanoi','Dy\'aketh','Elsy\'eir','Fal\'shia','Fe\'saan','Fi\'rios','Ke\'lshan','Kor\'tal','Ksi\'m\'yen','N\'dras','Tash\'var','T\'au\'n','T\'olku','Uan\'Voss','Vash\'ya','Velk\'Han','Yo\'vai']
# In a separate table so the app doesn't falsely assert each sept is a single planet.
sept_records=[{'name':name,'location_kind':'tau_sept_or_system','source_url':'https://wh40k.lexicanum.com/wiki/Sept_Symbol','planetary_body_confirmed':False,'source_review':'Index records these as septs, not necessarily planets.'} for name in TAU_SEPT_SYSTEMS]
# Link a few sector/planet associations that were *confirmed* by named sector index.
assert len({w['id'] for w in locations})==len(locations)
for w in locations:
 if w['sector_id'] and w['sector_id'] in bysec:
  seg=bysec[w['sector_id']]['segmentum']
  if seg and w.get('segmentum') and seg!=w['segmentum']:
   # preserve conflict without making an invalid geography
   w.setdefault('geography_conflict',f'World listed {w["segmentum"]} but sector index places {w["sector_id"]} in {seg}.')
   w['segmentum']=None
# Verified clarifications from Necron index / sector index
for name,sector in [('Damnos','Vidar'),('Medusa','Medusan'),('Mordia','Stygius'),('Kronus','Lithesh'),('Mandragora','Vidar'),('Chogoris','Yasan'),('Krieg','Uhulis')]:
 w=byworld.get(name.casefold())
 if w:
  sid=slug(sector);assert sid in bysec
  w['sector_id']=sid
  if bysec[sid]['segmentum'] and (not w.get('segmentum') or w.get('segmentum')==bysec[sid]['segmentum']):w['segmentum']=bysec[sid]['segmentum']
  w.setdefault('indexed_attestations',[]).append(S if name not in ('Mandragora',) else T)
# Source citations and audit dataset
for s in sectors:
 s['source_list_url']=S
for w in locations:
 if w['surface'] in ('Unspecified.','Unspecified'):
  w['surface']='Unknown; not documented in reviewed reference.'
 if w['atmosphere'] in ('Unspecified.','Unspecified'):
  w['atmosphere']='Unknown; not documented in reviewed reference.'
 if w['name']=='Schrödinger VII':w.setdefault('geography_note','Vidar source index explicitly identifies this as a Necron-occupied former human world.')
# Important: one seed record named Macharia in Cadian system, a different Macharia in Donia Magna system;
# former remains, new latter distinguished with a qualified name to avoid conflation.
newworld('Macharia (Donia Magna System)','Shrine World','Pacificus','','Birthplace of Lord Solar Macharius, originally named Donia.','Imperium','planet',P)
# Sector system table enrichment (system names explicitly present in the indexed sectors list)
SYS='''
Piscina|Abiaus
Roxanzand|Chelio
Gerat|Chiros
Kalidar|Chiros
Pandorax|Demeter
Lycanthos|Fourth Quadrant
Silurian|Gorath
Kaurava|Lithesh
Rynnstar|Loki
Freiya|Loki
Istrouman|Macharius Alpha
Cernis|Magulanox
Quintus|Magulanox
Nachmund|Nachmund
Vigilus|Nachmund
Sexton|Sexton
Betalis|Talis Munus
Konor|Ultima
Masali|Ultima
Talasa|Ultima
Veridia|Ultima
Gartuli|Yasan
Thaxis|Yasan
'''.strip()
knownsys={(r['name'].casefold(),r.get('sector_id')) for r in systems}
for line in SYS.splitlines():
 n,sec=line.split('|');ident=slug(sec+'-'+n)
 if (n+' System',slug(sec)) not in knownsys:
  systems.append({'id':ident,'name':n+' System','sector_id':slug(sec),'subsector_id':None,'source_url':S,'review_state':'index_only','membership_confidence':'sector_index'})
# Add source-level methodology, don't promise impossible full enumeration.
d['sources'] += [
 {'name':'Lexicanum Necron Tomb Worlds index','url':T,'scope':'Selected known Necron worlds and dynastic affiliation'},
 {'name':'Lexicanum Tau sept naming index','url':'https://wh40k.lexicanum.com/wiki/Sept_Symbol','scope':'Septs/systems, not all verified planets'},
 {'name':'Lexicanum Planets of Calixis','url':CAL,'scope':'Follow-up completeness target'}]
d['version']='0.5-expanded-index-2026-10-12';d['title']='Warhammer 40,000 Galactic Atlas — Expanded Research Index'
d['scope']='Expanded cited named-world and sector index; incomplete by design. Not all published planets/sectors, and not every world has a verified individual factsheet.'
d['research_date']='2026-10-12';d['research_method']='Human-reviewed sample transcription of Lexicanum sector, general planet, and tomb-world indexes; no wiki crawling or automated full-index extraction.'
d['source_specific_limitations']=['Individual source book pages not checked for all index-only entries','Atmospheric chemistry and geographic coordinates very rarely described in index','Lexicanum has citation warnings and wiki updates may alter canon interpretation','This atlas is not an exhaustive record of every named world']
d['tau_sept_names_not_verified_planets']=sept_records
# Good data lineage: source URL for each entry, plus editorial note and census
record_counts=collections.Counter(w['factsheet_completeness'] for w in locations)
d['coverage']={'named_sectors_and_regional_rows':len(sectors),'named_subsector_and_subregion_rows':len(subsectors),'named_system_rows':len(systems),'named_location_rows':len(locations),'index_only_locations':record_counts.get('index_only',0),'curated_partial_locations':record_counts.get('curated_partial',0),'fully_environmentally_verified_planets':0,'completeness_claim':False}
# Additional export: editable audit data so reviewing primary sources is easy.
audit=[{'name':w['name'],'source':w['source_url'],'index_source':w.get('source_list_url') or '', 'type':w['world_type'],'sector_id':w['sector_id'] or '', 'segmentum':w['segmentum'] or '', 'review_state':w['review_state'],'factsheet_completeness':w['factsheet_completeness'],'atmosphere_known':not w['atmosphere'].lower().startswith(('unknown','unspecified','not consistently')), 'surface_known':not w['surface'].lower().startswith(('unknown','unspecified')), 'coordinates_known':w.get('coordinates_verified',False),'eye_relation':w['eye_relation'],'rift_side':w['rift_side']} for w in locations]

def save_csv(file,rows):
 cols=list(dict.fromkeys(k for r in rows for k in r))
 with (R/file).open('w',encoding='utf-8-sig',newline='') as fp:
  writer=csv.DictWriter(fp,fieldnames=cols);writer.writeheader()
  for r in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
(R/'atlas_data.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
for f,data in [('locations.csv',locations),('sectors.csv',sectors),('subsectors.csv',subsectors),('systems.csv',systems),('primarch_homeworlds.csv',d['primarchs']),('source_audit.csv',audit),('tau_sept_systems.csv',sept_records)]:save_csv(f,data)
# the existing app is still fully offline, uses latest data and supports text export.
app=(R/'atlas_template.html').read_text(encoding='utf-8').replace('__ATLAS_JSON__',json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
(R/'atlas.html').write_text(app,encoding='utf8')
readme=f'''# Warhammer 40,000 Galactic Atlas — Research Expansion

## Indexed coverage as of 12 October 2026

- **{len(sectors)}** sector and distinct named region records (not all true Imperial sectors)
- **{len(subsectors)}** subsectors and other named subregions
- **{len(systems)}** star-system records
- **{len(locations)}** unique named planet, moon, habitat and other location records
- **{record_counts.get('index_only',0)}** additional `index_only` location records with skeletal factsheets; **{record_counts.get('curated_partial',0)}** edited seed factsheets
- 20 Primarch homeworld lines, including deliberately unresolved entries
- **No** real-space canonical coordinates claimed and **no** claim of completeness.

## Files

- `atlas.html`: self-contained interactive viewer with era overlays, sector and location search, factsheets, and JSON/CSV exports. Open locally in a browser.
- `atlas_data.json`: canonical editable project database.
- `sectors.csv`, `subsectors.csv`, `systems.csv`, `locations.csv`: machine-readable hierarchy.
- `source_audit.csv`: review queue with index-only/curated states, source URL, missing atmosphere and map position flags.
- `tau_sept_systems.csv`: named T'au septs that should **not** automatically be treated as planetary bodies.
- `primarch_homeworlds.csv`: primarch/world lookup, moon and unknown notes retained.

## How this pass was researched

The Lexicanum [sector index]({S}), [planet index]({P}), [Necron tomb world index]({T}), and [Tau sept list](https://wh40k.lexicanum.com/wiki/Sept_Symbol) were checked on 2026-10-12. Some source-linked index entries have uncertain citation status; source-level review is pending. For any record drawn only from an index, attributes are explicitly unknown unless specified in that index. Desert/ocean/ice etc. surface descriptions are **only interpretations of the stated WORLD TYPE**, not separately verified environmental facts. In particular, climate/chemical atmosphere is *not* deduced from a general world type.

`Sectors` include several comparable-looking **regions, reaches, cluster names and border sectors**; consult `category`. Some sector/segmentum assignments change with editions or are unsettled, e.g. Fenris in some sources, and Stygius near the Obscurus/Ultima border. A few named locations are station/rift descriptions and should not be plotted as physical planets; such entries are separately typed or omitted.

## Accuracy and remaining work

These are deliberately **indexed, not exhaustive**. The general planet list currently spans over 3,000 rendered lines of entries and sources and we did not transcribe every line; many additional planets still remain. Even recording every name in an article is not 'all planets' in-universe. Prioritize broad A–Z harvesting with pagination-aware licensed ingestion, deduplicate renamed worlds, identify planet vs station/ship/moon, traverse category pages and sector-specific gazetteers, and check original GW/FW/Black Library/FFG books for every atmosphere, surface, sovereign date and faction. Many entries will never have a fully specified atmosphere. Scientific simulation must remain optional and clearly non-canonical.

For maps, only plot coordinates whose source and reference frame are documented. The Eye of Terror dates to the Fall of the Aeldari, while the Cicatrix Maledictum follows the 13th Black Crusade. Preserve historical identity rather than inventing previous eye/warp Rift states of worlds.

Unofficial fan-made research project. Warhammer 40,000 © Games Workshop. Summaries are paraphrased and sources linked; no prose from reference articles copied into database in bulk.
'''
(R/'README.md').write_text(readme,encoding='utf8')
zipname=Path('/mnt/data/warhammer40k_galactic_atlas_expanded.zip')
with zipfile.ZipFile(zipname,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for nm in ['atlas.html','atlas_data.json','locations.csv','sectors.csv','subsectors.csv','systems.csv','source_audit.csv','tau_sept_systems.csv','primarch_homeworlds.csv','README.md','atlas_template.html','enrich_research.py','build.py']:
  z.write(R/nm,arcname='warhammer40k_atlas/'+nm)
print(json.dumps({'sector_rows':len(sectors),'subsector_rows':len(subsectors),'system_rows':len(systems),'world_rows':len(locations),'index_only':record_counts.get('index_only',0),'world_conflicts':[(w['name'],w.get('geography_conflict')) for w in locations if w.get('geography_conflict')][:15], 'zip_bytes':zipname.stat().st_size},indent=2))
