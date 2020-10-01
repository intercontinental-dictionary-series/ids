import unicodedata
import re

cyrill2phonemic_lgs = list(range(26, 36)) + list(range(37, 43))\
                + list(range(50, 53)) + list(range(54, 76))\
                + [80, 81, 107, 160, 162, 164, 165, 166, 316, 317]\
                + list(range(500, 535))


def norm(f, desc, lid):
    """
    Normalize systematic issues
    """
    f_ = re.sub(r'[’‘′´]', 'ʼ', f.strip())
    for s, r in [
                ('\u007f', ''),
                ('\uf11e', '\ufffd'),
                ('\uf8ff', '\ufffd'),
                ('\u2028', ' '),
                (' )', ')')
            ]:
        f_ = f_.replace(s, r)
    if desc and desc.lower() == 'phonemic' and int(lid) in cyrill2phonemic_lgs:
        for s, r in [
                    ("'", 'ʼ'),
                    ('ћ', 'ħ'),
                    ('ӡ', 'ʒ'),
                    ('‰', 'ä'),
                    ('ﬁ', 'ˤ'),
                    ('Ɂ', 'ʔ'),
                    ('ӣ', 'ī'),
                    ('ё', 'ö'),
                    ('ť', 'tʼ'),
                    ('t̛', 'tʼ'),
                    ('q̛', 'qʼ'),
                    ('k̛', 'kʼ'),
                    ('Ι', 'ʕ'),
                    ('λ', 'ɬ'),
                    ('č̛', 'čʼ'),
                    ('c̛', 'cʼ')
                ]:
            f_ = f_.replace(s, r)
        # replace cyrillic letters which should be latin one
        # and decompose them in beforehand
        f_ = unicodedata.normalize('NFD', f_)
        for s, r in [
                    ('е', 'e'),
                    ('а', 'a'),
                    ('о', 'o'),
                    ('х', 'x'),
                    ('у', 'u'),
                    ('с', 'c')
                ]:
            f_ = f_.replace(s, r)
    return unicodedata.normalize('NFC', f_)


def preprocess_form_comment(f, desc, lid, com, pid):
    """
    Correct/clean systematic issues with comments and normalize forms
    """

    def cc(str, s):
        return '{0}{1}{2}'.format(str if str else '', ' ' if str else '', s)

    f_ = norm(f, desc, lid)
    com_ = com.replace('\u2028', ' ')
    com_ = com_.replace('\u00a0', '')
    com_ = com_.replace('\u007f', '')
    com_ = com_.replace('( ', '(')
    com_ = com_.replace(' )', ')')

    # catch final (?)
    if re.search(r' ?\(\?\)$', f_):
        f_ = re.sub(r' ?\(\?\)$', '', f_)
        com_ = cc(com_, '(?)')

    # catch check p.20
    if f_.endswith(' check p.20'):
        f_ = f_.replace(' check p.20', '')
        com_ = cc(com_, 'check p.20')

    # catch (sb.)
    if f_.endswith(' (sb.)'):
        f_ = f_.replace(' (sb.)', '')
        com_ = cc(com_, '(sb.)')

    # catch (f.)
    if f_.endswith(' (f.)'):
        f_ = f_.replace(' (f.)', '')
        com_ = cc(com_, '(f.)')

    # catch (m.)
    if f_.endswith(' (m.)'):
        f_ = f_.replace(' (m.)', '')
        com_ = cc(com_, '(m.)')

    # catch (T(+...))
    m = re.findall(r'( *(\( *T\.?(\+N.?)?\)) *$)', f_)
    if m and len(m[0]) == 3:
        f_ = f_.replace(m[0][0], '')
        com_ = cc(com, m[0][1])

    # catch (N(+...))
    m = re.findall(r'( *(\( *[NK]\.?\+ *T\.?\)) *$)', f_)
    if m and len(m[0]) == 2:
        f_ = f_.replace(m[0][0], '')
        com_ = cc(com_, m[0][1])

    return f_.strip(), com_.strip()


# Standardized names and fixed Glottolog codes
LANGS = {}
for lang in """
26	Avar (Dialect Batlukh)	Avar (Batlukh dialect)	ava		avar1256	batl1238
27	Avar (Dialect Hid)	Avar (Hid dialect)	ava		avar1256	hidd1238
28	Avar (Dialect Andalal)	Avar (Andalal dialect)	ava		avar1256	anda1281
29	Avar (Dialect Antsukh)	Avar (Antsukh dialect)	ava		avar1256	ancu1238
30	Avar (Dialect Zakataly)	Avar (Zakataly dialect)	ava		avar1256	zaka1239
31	Avar (Dialect Karakh)	Avar (Karakh dialect)	ava		avar1256	kara1473
33	Akhvakh (Northern Akhvakh)	Akhvakh (Northern dialect)	akv		akhv1239
34	Akhvakh (Southern Akhvakh)	Akhvakh (Southern dialect)	akv		akhv1239
35	Bagvalin	Bagvalal	kva		bagv1239
38	Ghodoberi	Godoberi	gdo		ghod1238
40	Karata Tokitin	Karata (Tokitin dialect)	kpt		kara1474	toki1238
41	Khvarshi (Khvarshi)	Khwarshi (Khwarshi dialect)	khv		khva1239	xvar1237
42	Hinukh	Hinuq	gin		hinu1240
54	Khvarshi (Dialect Inxokvari)	Khwarshi (Inkhokvari dialect)	khv		khva1239	inxo1238
55	Tsez (Dialect Sagadin)	Tsez (Sagada dialect)	ddo		dido1241	saga1261
58	Dargwa (Dialect Itsari)	Dargwa (Itsari dialect)	dar		darg1241	icar1234
59	Dargwa (Dialect Kubachi)	Dargwa (Kubachi dialect)	dar		darg1241	kuba1248
60	Dargwa (Dialect Khajdak)	Dargwa (Khajdak dialect)	dar		darg1241	kajt1238
62	Archi (Variant 1)	Archi (variety 1)	aqc		arch1244
64	Lezgi	Lezgian	lez		lezg1247
65	Lezgi (Dialect Mikrakh)	Lezgi (Mikrakh dialect)	lez		lezg1247
67	Tabassaran (Dialect North Tabasaran - Khanag)	Tabasaran (Northern dialect Khanag subdialect)	tab		taba1259
68	Tabassaran (Dialect South Tabasaran)	Tabasaran (Southern dialect)	tab		taba1259	sout2752
71	Azerbaijan	Azerbaijani	azj		nort2697
74	Tats	Judeo-Tat	jdt		jude1256
81	Avar (Dialect Kusur)	Avar (Kusur dialect)	ava		avar1256
126	Erza Mordvin	Erzya Mordvin	myv		erzy1239
127	Estonian	Estonian	est		esto1258
143	Lappish (North Saami)	Northern Saami	sme		nort2671
162	Tsez (Dialect Mokok)	Tsez (Mokok dialect) 	ddo		dido1241
164	Dargwa (Dialect Muiri)	Dargwa (Muiri dialect)	dar		darg1241
165	Lezgi (Dialect Kuba)	Lezgian (Quba dialect)	lez		lezg1247	quba1246
166	Azerbaijan (Dialect Terekeme)	Azerbaijani (Terekeme dialect)	azj		nort2697
167	Greek (Ancient)	Ancient Greek 	grc		anci1242
168	Greek (Modern)	Modern Greek	ell		mode1248
174	Carib (De'kwana)	De'kwana	mch		maqu1238
180	Irish (Old)	Old Irish	sga		oldi1245
185	Norse (Old)	Old Norse	non		oldn1244
188	English (Old)	Old English	ang		olde1238
189	English (Middle)	Middle English	enm		midd1317
192	German (Old High)	Old High German	goh		oldh1241
193	German (Middle High)	Middle High German 	gmh		midd1343
198	Prussian (Old)	Old Prussian	prg		prus1238
199	Slavonic (Old Church)	Old Church Slavonic	chu		chur1257
205	Albanian, Tosk	Albanian (Tosk variety)	als		tosk1239
206	Armenian, Eastern	Armenian (Eastern variety)	hye		nucl1235
207	Armenian, Western	Armenian (Western variety)	hye		homs1234
209	Tokharian A	Tocharian A	xto		tokh1242
210	Tokharian B	Tocharian B	txb		tokh1243
215	Aramaic (Ancient)	Ancient Aramaic		oar	olda1245
218	Jamaican Creole English (Dialect Limonese Creole)	Jamaican Creole (Limonese Creole dialect)	jam		jama1262
222	Nahuatl (Sierra de Zacapoaxtla)	Nahuatl (Sierra de Zacapoaxtla variety)	azz		high1278
223	Chatino, Zacatepec	Chatino (Zacatepec variety)	ctz		zaca1242
227	Haida (Northern)	Northern Haida	hdn		nort2938
230	Nootka	Nuu-chah-nulth	noo	nuk	noot1239	nuuc1236
232	Chehalis (Upper)	Upper Chehalis	cjh		uppe1439
252	Ninam (Shirishana)	Ninam (Shirishana variety)	shb		nina1238
298	Sanapan√° (Dialect Angait√©)	Sanapaná (Angaité dialect)	sap		sana1298	anga1316
299	Sanapan√° (Dialect Enlhet)	Sanapaná (Enlhet dialect)	sap		sana1298
300	Lengua	Lengua		leng1262	leng1262
316	Andi Dialect Muni	Andi (Muni dialect)	ani		andi1255	muni1255
317	Chechen (Dialect Akkin)	Chechen (Akkin dialect)	che		chec1245
318	Ghulfan	Uncunwee	ghl		ghul1238
320	Avar (Dialect Araderikh)	Avar (Araderikh dialect)	ava		avar1256
321	Avar (Dialect Khunzakh)	Avar (Khunzakh dialect)	ava		avar1256	kunz1243
322	Avar (East Dialect Gergebil)	Avar (East Gergebil dialect)	ava		avar1256
323	Avar (Dialect Ansalta)	Avar (Ansalta dialect)	ava		avar1256
324	Avar (Dialect Salatav)	Avar (Salatav dialect)	ava		avar1256	sala1265
325	Khvarshi (Dialect Kwantlada)	Khwarshi (Kwantlada dialect)	khv		khva1239
401	Central-Thai	Central Thai	tha		thai1261
402	Southern Tai of Songkhla	Southern Tai (Songkhla variety)	sou		sout2746
403	Thai (Dialect Korat)	Thai (Korat variety)	sou		sout2746
404	Khamuang of Chiang Mai	Khamuang (Chiang Mai variety)	nod		nort2740
407	Tai Lue	Tai Lü	khb		luuu1242
408	Tai Khuen	Tai Khün	kkh		khun1259
421	Li of Baoding	Hlai (Baoting variety)	lic		hlai1239
500	Aghul (Dialect Koshan)	Aghul (Koshan dialect)	agx		aghu1253	kosh1245
501	Botlikh (Dialect Miarso)	Botlikh (Miarso dialect)	bph		botl1242
502	Chamalal (Dialect Gigatli)	Chamalal (Gigatli dialect)	cji		cham1309	giga1238
503	Dargwa (Dialect Chirag)	Dargwa (Chirag dialect)	dar		darg1241	chir1284
504	Dargwa (Dialect Gapshima Shukti)	Dargwa (Gapshima Shukti dialect)	dar		darg1241
505	Dargwa (Dialect Gapshima)	Dargwa (Gapshima dialect)	dar		darg1241
506	Dargwa (Dialect Gubden)	Dargwa (Gubden dialect)	dar		darg1241
507	Dargwa (Dialect Kadar)	Dargwa (Kadar dialect)	dar		darg1241
508	Dargwa (Dialect Megeb)	Dargwa (Megeb dialect)	dar		darg1241
509	Dargwa (Dialect Mekegi)	Dargwa (Mekegi dialect)	dar		darg1241
510	Dargwa (Dialect Mugi)	Dargwa (Mugi dialect)	dar		darg1241
511	Dargwa (Dialect Sirkhi)	Dargwa (Sirkhi dialect)	dar		darg1241
512	Dargwa (Dialect Tsudakhar sub Tanty)	Dargwa (Tsudakhar dialect, Tanty subdialect)	dar		darg1241	cuda1238
513	Dargwa (Dialect Tsudakhar)	Dargwa (Tsudakhar dialect)	dar		darg1241	cuda1238
514	Dargwa (Dialect Urakhi)	Dargwa (Urakhi dialect)	dar		darg1241	urax1238
515	Dargwa (Dialect Usisha)	Dargwa (Usisha dialect)	dar		darg1241
517	Bezhta (Dialect Khasharkhota)	Bezhta (Khasharkhota dialect)	kap		bezh1248	khoc1238
519	Kumyk (Dialect Dorgeli)	Kumyk (Dorgeli dialect)	kum		kumy1244
520	Kumyk (Dialect Kajtak Tumenler)	Kumyk (Kajtak Tumenler dialect)	kum		kumy1244
521	Kumyk (Dialect Kajtak)	Kumyk (Kajtak dialect)	kum		kumy1244
522	Kumyk (Dialect Karabudakhkent)	Kumyk (Karabudakhkent dialect)	kum		kumy1244
523	Kumyk (Dialect Ter Bragun)	Kumyk (Ter Bragun dialect)	kum		kumy1244
524	Lak (Dialect Arakul)	Lak (Arakul dialect)	lbe		lakk1252
525	Lak (Dialect Balkhar)	Lak (Balkhar dialect)	lbe		lakk1252
526	Lak (Dialect Shali)	Lak (Shali dialect)	lbe		lakk1252
527	Rutul (Borchino Khnow)	Rutul (Borchino Khnow dialect)	rut		rutu1240
528	Rutul (Ikhrek)	Rutul (Ikhrek dialect)	rut		rutu1240	ixre1238
529	Rutul (Mukhrek)	Rutul (Mukhrek) dialect	rut		rutu1240	ixre1238
530	Rutul (Shinaz)	Rutul (Shinaz dialect)	rut		rutu1240	shin1265
531	Bezhta (Dialect Tljadal sub Karauzek)	Bezhta (Tlyadal dialect, Karauzek subdialect)	kap		bezh1248	tlya1238
532	Tsakhur (Dialect Gelmets)	Tsakhur (Gelmets dialect)	tkr		tsak1249
534	Archi (Variant 2)	Archi (variety 2)	aqc		arch1244
704	Mahasu Pahari (Dialect Kotghari)	Mahasu Pahari (Kotghari dialect)	bfz		maha1287
827	Ahlao Th	Ahlao (Thavung)	thm	thm	aheu1239	aheu1239
""".split('\n'):
    if lang:
        t = lang.split('\t')
        if len(t) == 6:
            t.append('')
        d = {}
        if t[2]:
            d['name'] = t[2]
        if t[3]:
            d['iso'] = t[3]
        if t[4]:
            d['iso'] = t[4]
        if t[5]:
            d['glotto'] = t[5]
        if t[6]:
            d['glotto'] = t[6]
        LANGS[int(t[0])] = d

"""
KME2	Kme-2	varieties of the language known as Kemie, among other names, Glottolog code manm1238.
SHJ	Bulang-2	blan1242
YDE	Bulang-3	blan1242
KME	Keme	varieties of the language known as Kemie, among other names, Glottolog code manm1238.
XU	Xu	Hu, Glottolog code huuu1240.
MNN	Mang’an B.
WA	Wa	nucl1290
RUM	Rumai	ruma1248
PRA	Prai	pray1239 / phai1238
PUS	Pusing	bitt1240; other names include Buxing, Bit, Khabit.
PLA	Paliu	boly1239
MLB	Mlabri	mlab1235
VIET	Vietnamese	viet1252
HAN	Hanoi Vn	nort2683
THM	Tho Mun
LIH	LiHa	varieties of Cuoi, Glottolog code cuoi1242.
TUM	Tum varieties of Cuoi, Glottolog code cuoi1242.
PHU	Phu Tho M
KHAP	Kha Poong	khap1242
MAL	Malieng	mali1278
AHL	Ahlao Th	aheu1239
NYAK	Nyakur	nyah1250
KAS	Kasong	suoy1242
SMR	Samre	samr1245
SONG	Chong	chon1284
SKM	Surin Khmer	suri1265
MNC	Mang Ch	mang1378
MNV	Mang VN	mang1378
"""
