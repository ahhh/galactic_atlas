import json,csv,re,html,os,random
from pathlib import Path
from urllib.parse import quote
ROOT=Path('/mnt/data/warhammer40k_atlas')
SEG=['Solar','Obscurus','Ultima','Pacificus','Tempestus']
SECTOR_INPUT='''
Abiaus|Obscurus|sector
Abrint||sector
Acteron||sector
Adraphane|Pacificus|sector
Agripinaa|Obscurus|sector
Amerikon|Tempestus|sector
Antian||sector
Aquitaine|Ultima|sector
Argonnes||sector
Armageddon|Solar|sector
Askellon|Obscurus|sector
Badab|Ultima|sector
Cadian|Obscurus|sector
Caïna||sector
Cal-Sek||region
Caligari|Tempestus|sector
Calixis|Obscurus|sector
Caradryad|Tempestus|sector
Charadon|Ultima|sector
Chelio||sector
Chiros|Tempestus|sector
Donian|Pacificus|sector
Donorian|Tempestus|sector
Duros||sector
Electif||sector
Ephialtis|Tempestus|sector
Fenris|Solar|sector
Gothic|Obscurus|sector
Helioret|Ultima|sector
Hodur|Ultima|sector
Inca|Ultima|sector
Instar||sector
Ixaniad|Obscurus|sector
Jericho|Ultima|sector
Kadus||sector
Karthago|Ultima|sector
Kiltor||sector
Korianis|Ultima|sector
Lithesh|Ultima|sector
Nephilim||sector
Orpheus||sector
Palatine||sector
Pandora||sector
Paramar||sector
Pegasus|Solar|sector
Priam||sector
Prospero|Ultima|sector
Red Scar|Ultima|disputed_sector_or_subsector
Reductus|Tempestus|sector
Scarus|Obscurus|sector
Solar|Solar|sector
Ultima|Ultima|sector
Vidar|Ultima|sector
Calaphrax Cluster||cluster
Endymion Cluster|Ultima|cluster
The Pale Stars|Ultima|region
Khymaran Drift|Ultima|region
''' .strip()
SECTORS=[]
for row in SECTOR_INPUT.splitlines():
 n,seg,kind=row.split('|')
 SECTORS.append(dict(id=re.sub(r'[^a-z0-9]+','-',n.lower()).strip('-'),name=n,segmentum=seg or None,category=kind,source='https://wh40k.lexicanum.com/wiki/List_of_sectors',confidence='listed',map_coordinates=None))
# sep: name | kind | segmentum | sector | class | faction | surface | atmosphere | significance | source
DATA='''
Terra|planet|Solar|Solar|Hive / Throne World|Imperium|Planet-spanning urbanization; much of the natural surface obscured.|Not consistently quantified in accessible references.|Birthplace of humanity; Emperor's throne and Imperial capital.|Terra
Mars|planet|Solar|Solar|Forge World|Adeptus Mechanicus|Industrial and red desert world with extensive manufactoria.|Unspecified.|Seat of the Cult Mechanicus; Segmentum Solar naval fortress.|Mars
Mercury|planet|Solar|Solar|Mining / Industrial World|Imperium|Heavily exploited Solar System world.|Unspecified.|Inner Solar System.|Mercury
Venus|planet|Solar|Solar|Industrial World|Imperium|Industrialized Solar System planet.|Unspecified.|Sol System world.|Venus
Jupiter|gas_giant|Solar|Solar|Gas Giant|Imperium|Gaseous giant; major Jovian orbital installations.|Unspecified.|Jovian shipyards and satellites.|Jupiter
Saturn|gas_giant|Solar|Solar|Gas Giant|Imperium|Gaseous giant; home to Titan moon.|Unspecified.|Saturnian facilities.|Saturn
Titan|moon|Solar|Solar|Fortress Moon|Grey Knights|Fortress-monastery complexes.|Unspecified.|Home of the Grey Knights; moon of Saturn, not a planet.|Titan
Uranus|gas_giant|Solar|Solar|Gas Giant|Imperium|Gaseous Solar System world.|Unspecified.|Sol System.|Uranus
Neptune|gas_giant|Solar|Solar|Gas Giant|Imperium|Gaseous Solar System world.|Unspecified.|Sol System.|Neptune
Pluto|dwarf_planet|Solar|Solar|Outer System World|Imperium|Cold outer Solar System body.|Unspecified.|Historic defenses of the Sol System.|Pluto
Cthonia|planet|Solar||Mining World / former Legion World|Imperium / Sons of Horus (historical)|Subterranean mines and hive-like settlements.|Unspecified.|World on which Horus grew up; devastated during the Horus Heresy.|Cthonia
Fenris|planet|Solar|Fenris|Death / Feral / Astartes World|Imperium / Space Wolves|Volcanic summer, flooding seas, long icy winters.|Extreme storms; composition unspecified.|Homeworld of Leman Russ and the Space Wolves; disputed segmentum in some sources.|Fenris
Armageddon|planet|Solar|Armageddon|Hive World|Imperium; contested by Orks and Chaos|Industrial hives, ash wastes, jungles and fire wastes.|Industrial pollution; precise composition unspecified.|Site of the Armageddon Wars; sector capital.|Armageddon
Vostroya|planet|Solar||Industrial World|Imperium|Industrial cities and manufactoria.|Unspecified.|Home of the Vostroyan Firstborn.|Vostroya
Gathalamor|planet|Solar||Shrine / Fortress World|Imperium|Imperial religious sites and fortifications.|Unspecified.|Battleground in the Indomitus Crusade.|Gathalamor
Caliban|planet|Obscurus||Former Death / Feudal / Legion World|Dark Angels (historical); Chaos (later)|Formerly vast forests sheltering monstrous beasts.|Unspecified.|Lion El'Jonson's homeworld; shattered after the Heresy, later reformed as Wyrmwood.|Caliban
Chemos|planet|Ultima|Aquitaine|Former industrial / Legion World|Emperor's Children (historical)|Former resource-strained industrial landscape.|Unspecified.|Fulgrim's adopted homeworld; destroyed in the Heresy era.|Chemos
Olympia|planet|||Civilised / Former Legion World|Iron Warriors (historical)|Mountainous city-states and fortress settlements.|Unspecified.|Perturabo's homeworld; devastated in the Heresy.|Olympia
Chogoris|planet|||Feral / Astartes World|White Scars|Steppes and plains with settled city-states.|Unspecified.|Jaghatai Khan's adopted homeworld; also Mundus Planus.|Chogoris
Inwit|planet|||Ice / Astartes World|Imperial Fists (historical)|Frozen world with severe polar conditions.|Unspecified.|Rogal Dorn's adopted homeworld and Inwit Cluster.|Inwit
Nostramo|planet|||Former Mining / Hive World|Night Lords (historical)|Light-starved mining cities and polluted industry.|Unspecified.|Konrad Curze's world; destroyed by the Night Lords.|Nostramo
Baal|planet|Ultima|Red Scar|Astartes Homeworld|Imperium / Blood Angels|Radiation-scarred, arid desert planet.|Unspecified.|Blood Angels Chapter homeworld; Sanguinius was raised on its moon.|Baal
Baal Primus|moon|Ultima|Red Scar|Irradiated Moon|Blood Angels (historical)|Devastated wastelands, formerly inhabited.|Unspecified.|One of Baal's two notable moons; formerly Baal Prime.|Baal_Primus
Baal Secundus|moon|Ultima|Red Scar|Irradiated / Feral Moon|Imperium / Blood Angels|Irradiated deserts and tribal settlements.|Unspecified.|Sanguinius's actual adopted homeworld; moon of Baal.|Baal_Secundus
Medusa|planet|||Death / Astartes World|Imperium / Iron Hands|Unstable tectonics; mountain ranges and harsh plains.|Unspecified.|Ferrus Manus's adopted homeworld; not Medusa V.|Medusa
Nuceria|planet|||Former Civilised World|World Eaters (historical)|Gladiatorial centers and later ruined settlements.|Unspecified.|Angron's adopted homeworld.|Nuceria
Macragge|planet|Ultima|Ultima|Astartes / Civilised World|Imperium / Ultramarines|Temperate mountains, cities, farmland and polar installations.|Unspecified.|Roboute Guilliman's adopted homeworld; capital of Ultramar.|Macragge
Ardium|planet|Ultima|Ultima|Hive World|Imperium|Dense urban hives.|Unspecified.|World in the Macragge System.|Macragge_System
Nova Thulium|planet|Ultima|Ultima|Agri World|Imperium|Agricultural regions.|Unspecified.|World in the Macragge System.|Macragge_System
Thulium|planet|Ultima|Ultima|Death World|Imperium|Hazardous terrain; details not stated.|Unspecified.|World in the Macragge System.|Macragge_System
Laphis|planet|Ultima|Ultima|Shrine World|Imperium|Ecclesiastical sites; environment not established.|Unspecified.|World in the Macragge System.|Macragge_System
Mortendar|planet|Ultima|Ultima|Fortress World|Imperium|Fortifications and military bastions.|Unspecified.|World in the Macragge System.|Macragge_System
Calth|planet|Ultima||Civilised / Ultramar World|Imperium / Ultramarines|Population sheltered in underground arcologies after surface devastation.|Surface rendered lethal during Betrayal at Calth.|Important Ultramar world; devastated during the Heresy.|Calth
Iax|planet|Ultima||Garden / Agri World (historical)|Imperium / Ultramar|Once fertile garden landscapes; later corrupted.|Unspecified.|Major setting of Plague Wars; transformed into a plague world temporarily.|Iax
Sotha|planet|Ultima||Astartes Homeworld|Imperium / Scythes of the Emperor|Settled world with historic Pharos installation.|Unspecified.|Pharos world; target of Tyranid attack.|Sotha
Prandium|planet|Ultima||Former Agricultural World|Imperium (former)|Formerly rich agricultural surface, later consumed.|Unspecified.|Devoured by Hive Fleet Behemoth.|Prandium
Barbarus|planet|||Death World / Former Legion World|Death Guard (historical)|Poisonous lowlands under mist-shrouded uplands.|Lethal toxic and poisonous mists.|Mortarion's adopted homeworld.|Barbarus
Prospero|planet|Ultima|Prospero|Former Dead / Astartes World|Thousand Sons / Chaos|Former scholarly cities; devastated surface, later reconstruction.|Unspecified.|Magnus's homeworld; burned in M31; repopulated in M42.|Prospero
Colchis|planet|Pacificus||Former Legion / Dead World|Word Bearers (historical)|Dry landscapes with holy cities and ancient temples.|Unspecified.|Lorgar's homeworld; destroyed 035.M31.|Colchis
Nocturne|planet|||Death / Astartes World|Imperium / Salamanders|Volcanic plateaus, earthquakes and ash deserts.|Ash-laden; chemical composition unspecified.|Vulkan's adopted homeworld; orbiting moon Prometheus.|Nocturne
Deliverance|moon|||Astartes Fortress Moon|Imperium / Raven Guard|Former mining moon dominated by fortress installations.|Unspecified.|Corvus Corax's adopted world; a moon of Kiavahr.|Deliverance
Kiavahr|planet|||Forge / Industrial World|Imperium|Industrial planet, extensive manufactoria.|Unspecified.|Planet orbited by Deliverance.|Kiavahr
Cadia|planet|Obscurus|Cadian|Former Fortress World|Imperium (historical); Chaos warzone|Fortress cities, militarised landscape, later shattered.|Unspecified.|Held Cadian Gate; destroyed during the Thirteenth Black Crusade.|Cadia
Agripinaa|planet|Obscurus|Agripinaa|Forge World|Adeptus Mechanicus|Forge complexes and industry.|Unspecified.|Important forge world near the Eye of Terror.|Agripinaa
Scintilla|planet|Obscurus|Calixis|Hive World|Imperium|Dense hive cities and contrasting wilderness.|Unspecified.|Capital of the Calixis Sector.|Scintilla
Sepheris Secundus|planet|Obscurus|Calixis|Feudal / Mining World|Imperium|Cold, stormy, snowy landscapes, vast mines and small polar seas.|Heavy cloud cover, stormy cold climate.|Principal mining world of Calixis.|Sepheris_Secundus
Iocanthos|planet|Obscurus|Calixis|War / Feral World|Imperium (contested)|Wilderness and battle-scarred landscapes.|Unspecified.|Important Calixis world producing ghostfire pollen.|Iocanthos
Malfi|planet|Obscurus|Calixis|Hive World|Imperium|Sprawling urbanized hives.|Unspecified.|Wealthy and politically important Malfian subsector world.|Malfi
Baraspine|planet|Obscurus|Calixis|Hive World|Imperium|Urban hives.|Unspecified.|Adrantis Sub-sector hive world.|Baraspine
Fenksworld|planet|Obscurus|Calixis|Hive World|Imperium|Urban hive complexes.|Unspecified.|Located in the Josian Reach.|Fenksworld
Solomon|planet|Obscurus|Calixis|World of the Imperium|Imperium|Unspecified.|Unspecified.|World in the Markayn Marches.|Solomon
Kulth|planet|Obscurus|Calixis|War World|Imperium / Severan Dominate (historical)|Battlefields and fortified settlements.|Unspecified.|Capital of the Periphery; Spinward Front fighting.|Kulth
Quaddis|planet|Obscurus|Calixis|Pleasure World|Imperium|Estates and cultivated resort landscapes.|Unspecified.|Calixis pleasure world.|Quaddis
Strank|planet|Obscurus|Calixis|Feral / Swamp World|Imperium|Extensive swamps.|Humid swampland climate; chemistry unspecified.|Known for the Stenchbeast.|Strank
Acreage|planet|Obscurus|Calixis|Feudal World|Imperium|Feudal estates; broader terrain unspecified.|Unspecified.|World of the Josian Reach.|Acreage
47 Kapella|planet|Obscurus|Calixis|War World|Imperium|War-torn areas.|Unspecified.|Located in Drusus Marches.|47_Kapella
88 Tanstar|planet|Obscurus|Calixis|Frontier World|Imperium|Unspecified.|Unspecified.|Located in Drusus Marches.|88_Tanstar
Goth|planet|Obscurus|Gothic|Forge World|Imperium / Mechanicus|Industrial forges.|Unspecified.|Forge world of the Gothic Sector.|Goth
Port Maw|space_station|Obscurus|Gothic|Naval Base / Space Station|Imperial Navy|Artificial station; no natural surface.|Artificial station environment.|Major Gothic Sector naval base; not a planet.|Port_Maw
Piscina IV|planet|Obscurus|Abiaus|Astartes / Civilised World|Imperium|Settled planet and military fortifications.|Unspecified.|Battle of Piscina IV.|Piscina_IV
Mordia|planet|Obscurus||Hive World|Imperium|Tidally-locked world with crowded dark-side hives.|Unspecified.|Home of the Mordian Iron Guard.|Mordia
Tanith|planet|Pacificus||Former Forest World|Imperium (former)|Dense forests and moving nalwood groves.|Unspecified.|Homeworld of Tanith First-and-Only; destroyed by Chaos.|Tanith
Tallarn|planet|||Desert World|Imperium|Radiation-baked deserts after Heresy-era devastation.|Unspecified.|Home of Tallarn Desert Raiders.|Tallarn
Krieg|planet|||Death / Siege World|Imperium / Death Korps|Atomic wastelands and underground habitation.|Hazardous from nuclear devastation.|Homeworld of the Death Korps of Krieg.|Krieg
Catachan|planet|||Death / Jungle World|Imperium|Extreme jungles teeming with dangerous fauna and plants.|Humid tropical environment; chemistry unspecified.|Home of Catachan Jungle Fighters.|Catachan
Necromunda|planet|||Hive World|Imperium|Mega-hives, ash wastes and chemical desert.|Industrial pollution and ash.|Major hive world; home of House gangs.|Necromunda
Valhalla|planet|||Ice World|Imperium|Extensive ice fields and frozen plains.|Unspecified.|Home of the Valhallan Ice Warriors.|Valhalla
Ryza|planet|Solar||Forge World|Adeptus Mechanicus|Extensive manufacturing and forge sites.|Unspecified.|Important Imperial forge world.|Ryza
Metalica|planet|Ultima|Charadon|Forge World|Adeptus Mechanicus|Factory-spanning surface, depleted biosphere.|Industrial exhaust; composition unspecified.|Principal forge world in Charadon Sector.|Metalica
Kapston|planet|Ultima|Charadon|Fortress World|Imperium|Heavy defensive installations.|Unspecified.|Metalican Gate / capital of Brezantius System.|Kapston
Badab Primaris|planet|Ultima|Badab|Hive World|Imperium / Astral Claws (historical)|Hive city complexes.|Unspecified.|Former Astral Claws homeworld; Badab Sector capital.|Badab_Primaris
Pyrantis|planet|Ultima|Badab|Molten World|Uninhabited / disputed|Molten surface.|Unspecified.|Badab I.|Badab_System
Rigeal|planet|Ultima|Badab|Dead World|Imperium (orbital facilities)|Lifeless terrain and orbital fleet yards.|Unspecified.|Badab III.|Badab_System
Badab Secundus|planet|Ultima|Badab|Dead World|Imperium|Lifeless surface.|Unspecified.|Badab IV.|Badab_System
Badab IV/B|moon|Ultima|Badab|Penal Colony Moon|Imperium|Prison settlements.|Unspecified.|Moon of Badab IV.|Badab_System
Lamius|gas_giant|Ultima|Badab|Gas Giant|Uninhabited|Gas giant.|Gaseous.|Badab V.|Badab_System
Sigma|planet|Ultima|Badab|Dead World|Uninhabited|Dead surface.|Unspecified.|Badab VI.|Badab_System
Badab VII|planet|Ultima|Badab|Wreck Graveyard|Uninhabited|Wreckage and derelicts.|Unspecified.|Badab VII.|Badab_System
Archaea IV|planet|Ultima|Badab|Agri World|Imperium|Agricultural estates.|Unspecified.|Badab Sector; Archaea System.|Badab_Sector
Jahga|moon|Ultima|Badab|Ice Moon / Astartes Homeworld|Imperium / Star Phantoms|Frozen moon.|Unspecified.|Current Star Phantoms homeworld.|Badab_Sector
T'au|planet|Ultima||T'au Homeworld / Sept Capital|T'au Empire|Hot, dry savannah, mountains, one major continent.|Hot and arid; composition unspecified.|Homeworld and capital of the T'au Empire.|T%27au_%28Planet%29
Vior'la|planet|Ultima||T'au Sept World|T'au Empire|Volcanic and harsh terrains.|Unspecified.|Major military sept of the T'au.|Vior%27la
Sa'cea|planet|Ultima||T'au Sept World|T'au Empire|Highly urbanized sept world.|Unspecified.|Major T'au sept world.|Sa%27cea
Bork'an|planet|Ultima||T'au Sept World|T'au Empire|Advanced scientific complexes.|Unspecified.|Research-oriented sept world.|Bork%27an
Dal'yth|planet|Ultima||T'au Sept World|T'au Empire|Trade centers and settlements.|Unspecified.|Multispecies commerce nexus of the T'au Empire.|Dal%27yth
Au'taal|planet|Ultima||T'au Sept World|T'au Empire|Settled sept world.|Unspecified.|A T'au sept world.|Au%27taal
Pech|planet|||Kroot Homeworld|Kroot / T'au Empire ally|Dense forests and jungles.|Unspecified.|Homeworld of the Kroot species.|Pech
Vespid|planet|||Vespid Homeworld|Vespid / T'au Empire ally|Unspecified.|Unspecified.|Homeworld of the Vespid species.|Vespid
Agrellan (Mu'gulath Bay)|planet|Ultima||Colonial / Contested World|Imperium / T'au Empire (historical)|Settlements scarred by campaign.|Unspecified.|Former Imperial Agrellan, renamed under T'au rule.|Agrellan
Mandragora|planet|Ultima|Vidar|Necron Tomb / Crownworld|Necrons / Sautekh Dynasty|Necron tomb complexes.|Unspecified.|Crownworld of Imotekh's Sautekh Dynasty.|Mandragora
Solemnace|artificial_planet|Ultima||Artificial Necron Tomb World|Necrons / Nihilakh / Trazyn|Nanomachine outer shell; huge galleries beneath.|Artificially generated atmosphere via orbiting mirrors.|Trazyn the Infinite's museum-world.|Solemnace
Damnos|planet|Ultima||Necron Tomb World (contested)|Necrons / Imperium (contested)|Buried Necron complexes, formerly Imperial settlements.|Unspecified.|Necron invasion and Ultramarines campaigns.|Damnos
Thanatos|planet|||Necron Tomb World|Necrons|Necron burial structures.|Unspecified.|Important Necron world.|Thanatos
Serenade|planet|||Necron / Former Human World|Necrons / humans (historical)|Tomb complexes and inhabited areas.|Unspecified.|Important setting of The Infinite and The Divine.|Serenade
Drazak|planet|||Necron Tomb World|Necrons / Flayed Ones|Necron tomb architecture.|Unspecified.|Bone Kingdom of the Flayed Ones.|Drazak
Charadon|planet|Ultima||Ork World / Empire Capital|Orks|Heavily Ork-controlled world; terrain unspecified.|Unspecified.|Center of the Ork Empire of Charadon; sector association not confirmed.|Charadon_%28Planet%29
Ullanor|planet|||Former Ork Empire Capital|Orks; Imperium (historical)|Battle-scarred Ork fortress world.|Unspecified.|World of the Ullanor Crusade; its later connection to Armageddon is a major historical plotline.|Ullanor
Octarius|planet|||Ork / Tyranid War World|Orks; Tyranids (invading)|Warfare-devastated landscapes.|Unspecified.|Core of the Octarius warzone.|Octarius
Angelis (Gorkamorka)|planet|||Ork World|Orks|Harsh wastelands and scrap-built settlements.|Unspecified.|Setting of Gorkamorka.|Angelis
Sicarus|planet|Obscurus||Daemon / Chaos World|Chaos / Word Bearers|Warp-distorted daemon landscapes.|Warp-corrupted environment; conventional atmosphere not established.|Word Bearers' principal daemon world.|Sicarus
Medrengard|planet|Obscurus||Daemon / Fortress World|Chaos / Iron Warriors|Fortress citadels and hellish industrial landscapes.|Warp-corrupted; composition unspecified.|Iron Warriors' fortress world in Eye of Terror.|Medrengard
Sortiarius|planet|Ultima||Daemon / Sorcerer World|Chaos / Thousand Sons|Sorcerous towers and warp-transformed ground.|Warp-tainted; ordinary atmosphere unspecified.|Planet of the Sorcerers; its location changes across eras.|Sortiarius
Plague Planet|planet|Obscurus||Daemon / Plague World|Chaos / Death Guard|Diseased marshes and corrupt fortifications.|Noxious plague atmosphere.|Mortarion's plague domain inside the Eye of Terror.|Plague_Planet
Eidolon|planet|Obscurus||Aeldari Crone / Daemon World|Chaos; Aeldari historical claims|Warp-distorted terrain.|Warp-corrupted.|Former Aeldari core world within the Eye of Terror.|Eidolon
Aktosha|planet|Obscurus||Aeldari Crone / Daemon World|Chaos; Aeldari historical claims|Warp-distorted surface.|Warp-corrupted.|Crone World in the Eye of Terror.|Aktosha
Valedor|planet|Ultima||Maiden World / War World|Aeldari; Tyranids (invading)|Formerly biodiverse maiden-world ecosystems.|Unspecified.|Battle of Valedor; Aeldari versus Tyranids.|Valedor
Commorragh|webway_city|||Webway Metropolis|Drukhari|Vast interlinked artificial city-realms; no planetary surface.|Controlled webway enclaves; no single planetary atmosphere.|Capital of the Drukhari; not a planet or fixed Milky Way location.|Commorragh
Ulthwé|craftworld|||Aeldari Craftworld|Asuryani Aeldari|Self-contained continent-scale voidship habitats.|Engineered ship habitat; not a planet.|Major Craftworld often near the Eye of Terror.|Ulthwe
Biel-Tan|craftworld|||Aeldari Craftworld|Asuryani Aeldari|Self-contained artificial voidship habitats.|Engineered ship habitat; not a planet.|Militant Aeldari craftworld, later fractured.|Biel-tan
Iyanden|craftworld|||Aeldari Craftworld|Asuryani Aeldari|Self-contained artificial voidship habitats.|Engineered ship habitat; not a planet.|Aeldari craftworld devastated by Tyranids.|Iyanden
Alaitoc|craftworld|||Aeldari Craftworld|Asuryani Aeldari|Self-contained artificial voidship habitats.|Engineered ship habitat; not a planet.|Known for Path of the Outcast and Rangers.|Alaitoc
Saim-Hann|craftworld|||Aeldari Craftworld|Asuryani Aeldari|Self-contained artificial voidship habitats.|Engineered ship habitat; not a planet.|Wild Rider clans.|Saim-Hann
Altansar|craftworld|||Aeldari Craftworld|Asuryani Aeldari|Artificial craftworld ship habitat.|Engineered ship habitat; not a planet.|Craftworld lost within Eye of Terror for millennia.|Altansar
Lugganath|craftworld|||Aeldari Craftworld|Asuryani Aeldari|Artificial craftworld ship habitat.|Engineered ship habitat; not a planet.|Important Aeldari craftworld with extensive corsair links.|Lugganath
Hydraphur|planet|Pacificus||Segmentum Fortress World|Imperium / Imperial Navy|Extensive military infrastructure.|Unspecified.|Naval fortress of Segmentum Pacificus.|Hydraphur
Cypra Mundi|planet|Obscurus||Segmentum Fortress World|Imperium / Imperial Navy|Major naval docks and population centers.|Unspecified.|Segmentum Obscurus naval fortress.|Cypra_Mundi
Kar Duniash|planet|Ultima||Segmentum Fortress World|Imperium / Imperial Navy|Imperial infrastructure and naval defenses.|Unspecified.|Naval fortress of Ultima Segmentum.|Kar_Duniash
Bakka|planet|Tempestus||Segmentum Fortress World|Imperium / Imperial Navy|Naval installations.|Unspecified.|Segmentum Tempestus naval fortress.|Bakka
Gryphonne IV|planet|Tempestus||Destroyed Forge World|Adeptus Mechanicus (historical)|Former colossal forge facilities, devoured.|Unspecified.|Forge world destroyed by Hive Fleet Leviathan.|Gryphonne_IV
Ophelia VII|planet|||Shrine World|Imperium / Ecclesiarchy|Shrines and religious cities.|Unspecified.|Ecclesiarchal seat and Adepta Sororitas importance.|Ophelia_VII
San Leor|planet|||Shrine / Founding World|Imperium / Adepta Sororitas|Sacred foundations and convent history.|Unspecified.|Site associated with the founding of the Adepta Sororitas.|San_Leor
Rynn's World|planet|Ultima||Astartes Homeworld|Imperium / Crimson Fists|Cultivated land, cities, and fortified installations.|Unspecified.|Crimson Fists homeworld; attacked by Orks.|Rynn%27s_World
Vigilus|planet|Obscurus||Sentinel / Hive World|Imperium and invading forces|Hives, wastelands, and strategic routes.|Unspecified.|Gateway of the Nachmund Gauntlet.|Vigilus
Phobian|planet|Tempestus|Reductus|Astartes Homeworld|Imperium / Dark Hunters|Fortress-monastery and inhabited terrain.|Unspecified.|Dark Hunters homeworld.|Reductus_Sector
Rapture|planet|Tempestus|Reductus|Former Knight World|Imperium (former)|World rendered lifeless by Hive Fleet Leviathan.|Unspecified.|Lost Knight World in the Reductus Sector.|Reductus_Sector
''' .strip()
WORLD=[]
for line in DATA.splitlines():
 vals=[v.strip() for v in line.split('|')]
 if len(vals)!=10: raise ValueError((len(vals),line))
 name,kind,seg,sector,cl,owner,surface,atm,note,slug=vals
 WORLD.append(dict(id=re.sub('[^a-z0-9]+','-',name.lower()).strip('-'),name=name,location_kind=kind,segmentum=seg or None,sector_id=re.sub(r'[^a-z0-9]+','-',sector.lower()).strip('-') if sector else None,world_type=cl,affiliation=owner,surface=surface,atmosphere=atm,notable=note,source_url='https://wh40k.lexicanum.com/wiki/'+slug,source_tier='Lexicanum secondary; consult cited primary sources',review_state='needs_primary_source_review',eye_relation='unknown',rift_side='unknown',position=None,era_status=dict(pre_eye='Earlier state not established',pre_rift='See historical notes; exact status may depend on century',post_rift='Post-Rift state not independently established'),history=[]))
# Ullanor is the same physical world later known as Armageddon, not an additional planet.
WORLD=[w for w in WORLD if w['name']!='Ullanor']
ID={w['name']:w for w in WORLD}
def mark(name,**kw):
 assert name in ID,name
 ID[name].update(kw)
for n in ['Sicarus','Medrengard','Plague Planet','Eidolon','Aktosha']:
 mark(n,eye_relation='inside')
for n in ['Cadia','Fenris','Agripinaa','Ulthwé']:
 mark(n,eye_relation='near')
for n in ['Terra','Mars']:
 mark(n,rift_side='Sanctus')
for n in ['Baal','Baal Primus','Baal Secundus']:
 mark(n,rift_side='Nihilus')
mark('Armageddon',aliases=['Ullanor'],historical_identity='Ullanor teleported into the Armageddon System during the War of the Beast; one physical planet, two historical names.',history=[{'era':'pre_rift','event':'Ullanor was relocated and renamed Armageddon in the post-Heresy era.'}],era_status={'pre_eye':'Earlier environmental or faction state not established','pre_rift':'Formerly called Ullanor; now Imperial hive world Armageddon.','post_rift':'Armageddon remains a major contested Imperial war world.'})
mark('Sortiarius',placements_by_era={'pre_eye':{'segmentum':None,'sector_id':None,'eye_relation':'unknown'},'pre_rift':{'segmentum':'Obscurus','sector_id':None,'eye_relation':'inside'},'post_rift':{'segmentum':'Ultima','sector_id':'prospero','eye_relation':'outside'}})
mark('Solemnace',atmosphere='Artificial atmosphere produced by an engineered system of mirrors.',review_state='cross_checked_secondary')
for n in ['T\'au','Sepheris Secundus','Fenris','Macragge','Prospero','Caliban','Cadia','Mandragora','Solemnace','Charadon','Armageddon','Baal','Baal Secundus','Colchis','Cthonia','Badab Primaris','Jahga','Port Maw','Valedor','Commorragh','Biel-Tan','Ulthwé','Metalica','Kapston','Phobian','Rapture','Goth']:
 if n in ID: mark(n,review_state='cross_checked_secondary')

EXTRA='''
Luna|moon|Solar|Solar|Civilised / Industrial / Military Moon|Imperium|Underground laboratories, industry, and military installations.|Unspecified.|Terra's moon; historical Selenar gene-cults and defense structures.|Luna
Phobos|moon|Solar|Solar|Martian Moon|Adeptus Mechanicus|Small rocky Martian satellite.|Unspecified.|Mars satellite.|Sol_System
Deimos|moon|Solar|Solar|Grey Knights Sub-moon|Grey Knights / Mechanicus|Former Mars moon transferred to orbit Titan.|Unspecified.|Now a satellite of Titan, once of Mars.|Sol_System
Prometheus|moon|Ultima||Astartes Fortress Moon|Imperium / Salamanders|Fortress-monastery and enormous orbital dock.|Unspecified.|Moon of Nocturne, Salamanders' fortress-monastery.|Prometheus
The Rock|space_station|||Mobile Fortress-Monastery / Caliban Fragment|Imperium / Dark Angels|Fortified remnant of Caliban, transformed into giant mobile vessel.|Shipboard life-support; no planetary air.|Mobile Dark Angels headquarters, not a planet.|The_Rock
St. Josmane's Hope|planet|Obscurus|Cadian|Former Prison World|Imperium (historical)|Former prison world, later destroyed.|Unspecified.|Destroyed during the 13th Black Crusade.|St._Josmane%27s_Hope
Macharia|planet|Obscurus|Cadian|Former Cadian System World|Imperium (historical)|Destroyed during the 13th Black Crusade.|Unspecified.|Cadian System planet destroyed in 999.M41.|Cadian_System
Ganymede|moon|Solar|Solar|Fortress Moon|Imperium|Jovian hub-fortress and defenses.|Unspecified.|Important moon of Jupiter.|Ganymede
Ceres|dwarf_planet|Solar|Solar|Mining / Asteroid Belt World|Imperium|Rocky dwarf planet and installations.|Unspecified.|Sol asteroid belt dwarf planet.|Sol_System
'''.strip()
for line in EXTRA.splitlines():
 vals=[v.strip() for v in line.split('|')]
 if len(vals)!=10:raise ValueError(vals)
 name,kind,seg,sector,cl,owner,surface,atm,note,slug=vals
 w=dict(id=re.sub('[^a-z0-9]+','-',name.lower()).strip('-'),name=name,location_kind=kind,segmentum=seg or None,sector_id=re.sub(r'[^a-z0-9]+','-',sector.lower()).strip('-') if sector else None,world_type=cl,affiliation=owner,surface=surface,atmosphere=atm,notable=note,source_url='https://wh40k.lexicanum.com/wiki/'+slug,source_tier='Lexicanum secondary; consult cited primary sources',review_state='cross_checked_secondary',eye_relation='unknown',rift_side='unknown',position=None,era_status=dict(pre_eye='Earlier state not established',pre_rift='See historical notes; exact status may depend on century',post_rift='Post-Rift state not independently established'),history=[])
 WORLD.append(w);ID[name]=w

# Era event records. Events with unknown dates are NOT extrapolated into a timeline.
EVENTS={
'Caliban':[('pre_rift','Shattered after the Horus Heresy; The Rock endured as a mobile fortress.'),('post_rift','Reconstituted as Wyrmwood in later Dark Angels lore; historic destruction is not its only status.')],
'Cadia':[('pre_rift','Imperial fortress and Cadian Gate bastion; shattered at the end of M41.'),('post_rift','Destroyed world; surviving Cadians continue to fight elsewhere.')],
'Prospero':[('pre_rift','Burned in M31 and long left devastated.'),('post_rift','Thousand Sons return and begin repopulating in M42.')],
'Sortiarius':[('pre_rift','The Planet of the Sorcerers lay within the Eye of Terror.'),('post_rift','Transported to the Prospero region; do not preserve a fixed geographic position.')],
'Colchis':[('pre_rift','Destroyed in 035.M31.'),('post_rift','Destroyed.')],
'Nostramo':[('pre_rift','Destroyed by Konrad Curze before the Horus Heresy.'),('post_rift','Destroyed.')],
'Chemos':[('pre_rift','Destroyed during the Horus Heresy.'),('post_rift','Destroyed.')],
'Tanith':[('pre_rift','Destroyed at the founding of the Tanith First-and-Only in M41.'),('post_rift','Destroyed.')],
'Gryphonne IV':[('pre_rift','Overrun and consumed by Hive Fleet Leviathan.'),('post_rift','Destroyed.')],
'Prandium':[('pre_rift','Consumed by Hive Fleet Behemoth in M41.'),('post_rift','Destroyed.')],
'Biel-Tan':[('pre_rift','Functioning craftworld.'),('post_rift','Craftworld fractured during the Ynnari upheaval; its people continue.')],
'Baal':[('pre_rift','Blood Angels Chapter homeworld.'),('post_rift','Survived the Devastation of Baal, within Imperium Nihilus.')],
}
for name,events in EVENTS.items():
 for era,value in events: ID[name]['era_status'][era]=value
 ID[name]['history']=[{'era':era,'event':txt} for era,txt in events]
# explicit revised annotations; not confident that 40k canon maps all sectors with a single named time.
mark('Fenris',segmentum_note='Conflicting sources place Fenris in Obscurus; Solar is used here based on Fenris Sector source.')
mark('Red Scar' if 'Red Scar' in ID else 'Baal',sector_note='Red Scar is designated sector OR subsector by conflicting sources.')
# not all locations are planetary. Do not infer fixed positions for mobile craftworlds.
VALID_KINDS={'planet','moon','dwarf_planet','gas_giant','artificial_planet','craftworld','webway_city','space_station'}
assert all(w['location_kind'] in VALID_KINDS for w in WORLD)
assert len(WORLD)==len({w['id'] for w in WORLD})
assert len(SECTORS)==len({s['id'] for s in SECTORS})
for w in WORLD:
 if w['sector_id']:
  assert w['sector_id'] in {s['id'] for s in SECTORS},w
  sec=next(s for s in SECTORS if s['id']==w['sector_id'])
  if w['segmentum'] and sec['segmentum'] and w['segmentum']!=sec['segmentum']:
   raise ValueError('Inconsistent sector assignment '+w['name'])
# Primarch index: Alpharius/Omegon and erased primarchs deliberately have no invented location.
PRIMARCHS=[
('Lion El\'Jonson','Caliban'),('Fulgrim','Chemos'),('Perturabo','Olympia'),('Jaghatai Khan','Chogoris'),('Leman Russ','Fenris'),('Rogal Dorn','Inwit'),('Konrad Curze','Nostramo'),('Sanguinius','Baal Secundus'),('Ferrus Manus','Medusa'),('Angron','Nuceria'),('Roboute Guilliman','Macragge'),('Mortarion','Barbarus'),('Magnus the Red','Prospero'),('Horus Lupercal','Cthonia'),('Lorgar Aurelian','Colchis'),('Vulkan','Nocturne'),('Corvus Corax','Deliverance'),('Alpharius/Omegon',None),('II Legion — expunged',None),('XI Legion — expunged',None)]
assert all(n is None or n in ID for p,n in PRIMARCHS)
for p,n in PRIMARCHS:
 if n:
  ID[n].setdefault('primarchs',[]).append(p)
# Optional hierarchy below sector. Do not synthesize unknown star systems or subsectors.
SUBSECTOR_INPUT="""
Solar|Sol
Armageddon|Armageddon
Fenris|Svarteldari
Cadian|Cadian
Calixis|Golgenna Reach
Calixis|Drusus Marches
Calixis|Adrantis
Calixis|Josian Reach
Calixis|Malfian
Calixis|Markayn Marches
Calixis|The Periphery
Calixis|Hazeroth
Charadon|Obolis
Prospero|Prospero
Badab|Badab
Ultima|Ultramar
""".strip()
SUBSECTORS=[]
for line in SUBSECTOR_INPUT.splitlines():
 sec,n=line.split('|');SUBSECTORS.append({'id':re.sub('[^a-z0-9]+','-',(sec+'-'+n).lower()).strip('-'),'name':n,'sector_id':re.sub('[^a-z0-9]+','-',sec.lower()).strip('-'),'source_url':'https://wh40k.lexicanum.com/wiki/List_of_sectors'})
SYSTEM_INPUT="""
Sol|Solar|Sol
Armageddon|Armageddon|Armageddon
Fenris|Fenris|Svarteldari
Cadian|Cadian|Cadian
Macragge|Ultima|Ultramar
Badab|Badab|Badab
Archaea|Badab|
Baal|Red Scar|
Brezantius|Charadon|Obolis
Forzare|Prospero|Prospero
Prospero|Prospero|Prospero
""".strip()
SYSTEMS=[]
for line in SYSTEM_INPUT.splitlines():
 n,sec,sub=line.split('|');SYSTEMS.append({'id':re.sub('[^a-z0-9]+','-',(sec+'-'+n).lower()).strip('-'),'name':n+' System','sector_id':re.sub('[^a-z0-9]+','-',sec.lower()).strip('-'),'subsector_id':re.sub('[^a-z0-9]+','-',(sec+'-'+sub).lower()).strip('-') if sub else None,'source_url':'https://wh40k.lexicanum.com/wiki/'+n.replace(' ','_')+'_System'})
def locate(names,sector,system,sub=None):
 sid=re.sub('[^a-z0-9]+','-',(sector+'-'+system).lower()).strip('-')
 subid=re.sub('[^a-z0-9]+','-',(sector+'-'+sub).lower()).strip('-') if sub else None
 assert sid in {x['id'] for x in SYSTEMS}
 for name in names:
  w=ID[name];assert w['sector_id']==re.sub('[^a-z0-9]+','-',sector.lower()).strip('-'),name
  w['system_id']=sid
  if subid:w['subsector_id']=subid
for w in WORLD:
 w.setdefault('system_id',None);w.setdefault('subsector_id',None)
locate(['Terra','Mars','Mercury','Venus','Jupiter','Saturn','Titan','Uranus','Neptune','Pluto','Luna','Phobos','Deimos','Ganymede','Ceres'],'Solar','Sol','Sol')
locate(['Armageddon'],'Armageddon','Armageddon','Armageddon')
locate(['Fenris'],'Fenris','Fenris','Svarteldari')
locate(['Cadia','St. Josmane\'s Hope','Macharia'],'Cadian','Cadian','Cadian')
locate(['Macragge','Ardium','Nova Thulium','Thulium','Laphis','Mortendar'],'Ultima','Macragge','Ultramar')
locate(['Badab Primaris','Pyrantis','Rigeal','Badab Secundus','Badab IV/B','Lamius','Sigma','Badab VII'],'Badab','Badab','Badab')
locate(['Archaea IV','Jahga'],'Badab','Archaea')
locate(['Baal','Baal Primus','Baal Secundus'],'Red Scar','Baal')
locate(['Kapston'],'Charadon','Brezantius','Obolis')
locate(['Prospero'],'Prospero','Forzare','Prospero')
for name,sub in [('Scintilla','Golgenna Reach'),('Sepheris Secundus','Golgenna Reach'),('Baraspine','Adrantis'),('Fenksworld','Josian Reach'),('Acreage','Josian Reach'),('Malfi','Malfian'),('Solomon','Markayn Marches'),('Kulth','The Periphery'),('47 Kapella','Drusus Marches'),('88 Tanstar','Drusus Marches')]:
 ID[name]['subsector_id']=re.sub('[^a-z0-9]+','-',('Calixis-'+sub).lower()).strip('-')
for x in WORLD:
 assert not x['system_id'] or x['system_id'] in {z['id'] for z in SYSTEMS}
 assert not x['subsector_id'] or x['subsector_id'] in {z['id'] for z in SUBSECTORS}
DB={
 'version':'0.2-research-seed',
 'title':'Warhammer 40,000 Galactic Atlas — Research Seed',
 'scope':'Curated sample of documented sectors and prominent locations; NOT a complete canonical galaxy inventory.',
 'accuracy_notice':'No canonical full-galaxy coordinates provided. Schematic map positions show segmentum grouping ONLY. Blank data means unknown, not absent.',
 'eras':[{'id':'pre_eye','label':'Before the Fall of the Aeldari','eye':False,'rift':False},{'id':'pre_rift','label':'M41 · Eye of Terror, before Great Rift','eye':True,'rift':False},{'id':'post_rift','label':'M42 · Eye + Great Rift','eye':True,'rift':True}],
 'sources':[{'name':'Lexicanum sector list','url':'https://wh40k.lexicanum.com/wiki/List_of_sectors'},{'name':'Lexicanum world list','url':'https://wh40k.lexicanum.com/wiki/Planets_(List)'},{'name':'Lexicanum primarch list','url':'https://wh40k.lexicanum.com/wiki/Primarch'},{'name':'Great Rift','url':'https://wh40k.lexicanum.com/wiki/Great_Rift'},{'name':'Eye of Terror','url':'https://wh40k.lexicanum.com/wiki/Eye_of_Terror'}],
 'segmenta':SEG,'sectors':SECTORS,'subsectors':SUBSECTORS,'systems':SYSTEMS,'locations':WORLD,
 'primarchs':[{'name':name,'homeworld_id':ID[home]['id'] if home else None,'assignment_note':'No canonical adopted world securely specified' if home is None else None} for name,home in PRIMARCHS],
 'region_notes':['Eastern Fringe, Koronus Expanse, Ghoul Stars, Halo Stars, Maelstrom Zone and other regions are NOT automatically sectors.','Imperial sector borders and xenos realms can overlap or change across eras.','The Eye of Terror formed during the Fall; the Cicatrix Maledictum arose after Cadia fell at the end of M41.','Craftworlds are mobile artificial habitats, Commorragh is in the Webway, and moons cannot be labeled as planets.']
}
(ROOT/'atlas_data.json').write_text(json.dumps(DB,ensure_ascii=False,indent=2),encoding='utf-8')
def write_csv(filename,items):
 import io
 keys=list(dict.fromkeys(k for row in items for k in row))
 with (ROOT/filename).open('w',newline='',encoding='utf-8-sig') as fp:
  out=csv.DictWriter(fp,fieldnames=keys)
  out.writeheader()
  for r in items:
   out.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
write_csv('locations.csv',WORLD)
write_csv('sectors.csv',SECTORS)
write_csv('systems.csv',SYSTEMS)
write_csv('subsectors.csv',SUBSECTORS)
write_csv('primarch_homeworlds.csv',DB['primarchs'])
(ROOT/'README.md').write_text(f'''# Warhammer 40,000 Galactic Atlas — curated prototype\n\n**Seed size:** {len(SECTORS)} sector / other region records; {len(WORLD)} notable-location records, including {sum(w['location_kind']=='planet' for w in WORLD)} ordinary planets, moons, craftworlds and non-planet sites.\n\n## Files\n- `atlas.html` — self-contained offline interactive prototype. Open in a browser.\n- `atlas_data.json` — primary extensible JSON catalog.\n- `locations.csv`, `sectors.csv`, `systems.csv`, `subsectors.csv` — import-friendly tables.\n- `primarch_homeworlds.csv` — 20 Legion/Primarch records, including unknowns; Sanguinius and Corax were raised on moons.\n\n## Accuracy\nThis is **not a list of all canon planets**, and the prototype galaxy schematic is **NOT a spatially accurate galactic map**. Most published worlds lack canonical galactic Cartesian coordinates. The schematic groups stars by segmentum, not coordinates; the Rift illustration is symbolic, not a calculated boundary. The Eye of Terror predates the Great Rift.\n\nThe source for each record is a *Lexicanum navigation link*, not a claim that all facts were verified against primary lore. `review_state=cross_checked_secondary` denotes particular references sampled during research; other entries need independent checking. Wiki entries may be inconsistent or evolving. Atmospheres not established by sources are explicitly `Unspecified`. Historical era state is recorded only when a described event is known. Never infer allegiance from proximity to a sector.\n\n**Known example of conflicting material:** Fenris is given in Segmentum Solar in the Fenris Sector entry, whereas certain codices put it in Obscurus. Red Scar is described as either sector or subsector. Caliban is reportedly reconstituted as Wyrmwood in recent lore. Prospero is again being settled in M42.\n\n## How to extend accurately\n1. Capture all named sectors from Lexicanum's sector index, preserving entries that are *not actually sectors* in `category`.\n2. Traverse all sub-sector pages and each sector's known-world table, then the A–Z Planets list. Link a world to a sector only where explicitly asserted.\n3. Read planetary infoboxes AND prose, recording atmosphere, climate, terrain, and sovereignty as separate sourced assertions, with source edition/page and dates.\n4. Store historically changing facts in separate events, not by overwriting present values.\n5. Only create coordinates from licensed official regional maps with documented anchors; otherwise leave position `null`.\n6. Verify each fact against published GW/FW/Fantasy Flight game lore if possible, and capture source conflicts.\n\n## Copyright/attribution\nWarhammer 40,000 is the intellectual property of Games Workshop. The catalog is a small, manually composed research seed with links and paraphrased descriptions, not a mass copy of community articles. Source links are included for fact checking.\n''',encoding='utf-8')
print('sectors',len(SECTORS),'locations',len(WORLD),'kinds', {k:sum(w['location_kind']==k for w in WORLD) for k in VALID_KINDS})

# Rebuild standalone viewer with inlined catalog (works offline).
template=(ROOT/'atlas_template.html').read_text(encoding='utf-8')
viewer=template.replace('__ATLAS_JSON__',json.dumps(DB,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
(ROOT/'atlas.html').write_text(viewer,encoding='utf-8')
