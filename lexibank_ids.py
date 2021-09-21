import os
import pathlib
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from itertools import groupby
from urllib.request import urlretrieve
from zipfile import ZipFile

import pylexibank
from clldutils.misc import nfilter
from clldutils.text import split_text_with_context
from csvw import dsv
from idspy import IDSDataset

GLOTTOCODE_UPDATES = {"sana1281": "sana1298", "pray1239": "phai1238", "samr1245": "somr1240"}
SOURCE_UPDATES = {"key1958-1964": "key19581964"}

empty = re.compile(r"^\s*(NULL|∅|[\s\-]*)$")
wrapped_in_brackets = re.compile(r"^[(\[][^\[\]()]+?[)\]]$")


class Dataset(IDSDataset):

    IDSDataset.form_spec.missing_data = (
        "?",
        "∅",
        "-",
        "--",
        "- -",
        "––",
        "???",
        "",
        "-666",
        "666",
        "\u2014",
        "\u02bc",
    )
    IDSDataset.form_spec.separators = ";,/~"
    IDSDataset.form_spec.replacements = [("[", ""), ("]", ""), ("<", ""), (">", "")]
    IDSDataset.form_spec.strip_inside_brackets = True

    dir = pathlib.Path(__file__).parent
    id = "ids"

    def cmd_download(self, args):
        url = "https://github.com/intercontinental-dictionary-series/ids-data/archive/master.zip"
        dname = str(self.raw_dir / "data.zip")
        urlretrieve(url, dname)
        with ZipFile(dname, "r") as zipf:
            for fileName in zipf.namelist():
                if fileName.endswith(".csv"):
                    zipf.extract(fileName, str(self.raw_dir))
        os.remove(dname)

        edited_path = self.raw_dir / 'edited'
        for xlsx_file in edited_path.glob('*.xlsx'):
            edited_path.xlsx2csv(xlsx_file)['Sheet'].rename(xlsx_file.with_suffix('.csv'))
            if not xlsx_file.with_suffix('.md').exists():
                args.log.warn('No contributor file found for {}'.format(xlsx_file))

    def ids_raw_read(self, table):
        raw_dir = self.raw_dir / "ids-data-master"
        fname = raw_dir / (table + ".all.csv")
        if not fname.exists():
            fname = raw_dir / (table + ".csv")
        return dsv.reader(fname, namedtuples=True)

    def split_counterparts(self, c):
        if wrapped_in_brackets.search(c):
            c = c[1:-1].strip()
        for word in split_text_with_context(
            c, separators=self.form_spec.separators, brackets=self.form_spec.brackets
        ):
            word = word.strip()
            if word and word not in self.form_spec.missing_data:
                if wrapped_in_brackets.search(word):
                    word = word[1:-1].strip()
                n_split = list(
                    split_text_with_context(
                        word, separators=self.form_spec.separators, brackets=self.form_spec.brackets
                    )
                )
                if len(n_split) > 0:
                    for w in n_split:
                        if w.strip() and w.strip() not in self.form_spec.missing_data:
                            yield w.strip()
                else:
                    yield word

    def cmd_makecldf(self, args):

        args.writer.add_sources()
        args.writer.add_concepts(id_factory=lambda c: c.attributes["ids_id"])
        entry_ids = [p["ID"] for p in args.writer.objects["ParameterTable"]]

        args.writer.cldf.add_component(
            dict(
                url="chapters.csv",
                tableSchema=dict(
                    columns=[
                        dict(name="ID", datatype="string", required=True),
                        dict(name="Description", datatype="string", required=True),
                    ],
                    primaryKey="ID",
                ),
            )
        )
        args.writer.write(**{"chapters.csv": self.ids_raw_read("chapter")})

        personnel = {"1": defaultdict(list), "2": defaultdict(list), "3": defaultdict(list)}

        ids_lgs = [lg for lg in self.ids_raw_read("lang") if lg.status == "0"]
        ids_lgs_ids = [lg.lg_id for lg in ids_lgs]

        # read edited core IDS data via csv files generated during cmd 'download' out of XLSX files
        edited_data = {}
        # edited_data := {file: csv_file_name, md: md_file_name, date: edit_date}
        edited_path = self.raw_dir / 'edited'
        for edited_data_filename in edited_path.glob('*.csv'):
            # XLSX file name must have a valid IDS language ID in it {foo-ID.csv}
            ed_lg_id = re.match(r'^.+?\-(\d+)', edited_data_filename.stem).group(1)
            if ed_lg_id not in ids_lgs_ids:
                args.log.warn('ID {} not known for edited data file {}'.format(
                    ed_lg_id, edited_data_filename))
                continue
            edited_data[ed_lg_id] = {}
            edited_data[ed_lg_id]['file'] = edited_data_filename
            # {foo-ID.md contains the meta data on the contributors}
            edited_data[ed_lg_id]['md'] = edited_data_filename.with_suffix('.md')
            # get the edit date out of the XLSX or md file
            try:
                edited_data[ed_lg_id]['date'] = datetime.fromtimestamp(
                    edited_data_filename.with_suffix('.xlsx').stat().st_mtime).strftime('%Y-%m-%d')
            except FileNotFoundError:
                edited_data[ed_lg_id]['date'] = datetime.fromtimestamp(
                    edited_data_filename.stat().st_mtime).strftime('%Y-%m-%d')

        sources = defaultdict(list)
        for lc in self.ids_raw_read("lang_compilers"):
            if lc.lg_id not in ids_lgs_ids or lc.name == "BIBIKO":
                continue
            lname = SOURCE_UPDATES.get(lc.name, lc.name)
            if lc.lg_id in edited_data:
                # edited data's md file contains structured data as in global 'CONTRIBUTORS.md'
                p = self.get_personnel(args, edited_data[lc.lg_id]['md'])
                personnel["1"][lc.lg_id] = p['data entry']
                personnel["2"][lc.lg_id] = p['author']
                personnel["3"][lc.lg_id] = p['consultant']
            else:
                if lc.what_did_id in ["1", "2", "3"]:
                    personnel[lc.what_did_id][lc.lg_id].append(lname)
                else:
                    assert int(lc.what_did_id) in [4, 395]
                    sources[lc.lg_id].append(lname.lower())

        data_desc = defaultdict(dict)
        for ld in self.ids_raw_read("x_lg_data"):
            lid = ld.lg_id.strip()
            if lid in edited_data:
                # edited data come with a clean csv structure;
                # additional column names are taken as representations
                edited_data[lid]['data'] = edited_path.read_csv(edited_data[lid]['file'], dicts=True)
                header = [h for h in edited_data[lid]['data'][0].keys()
                          if h.strip().lower() not in ['chapter', 'entry', 'english', 'comment']]
                edited_data[lid]['reprs'] = []
                for i, h in enumerate(header):
                    data_desc[lid][str(i + 1)] = h.strip()
                    edited_data[lid]['reprs'].append(h.strip())
            else:
                data_desc[lid][ld.map_ids_data] = ld.header.strip()

        altnames = defaultdict(list)
        for n in self.ids_raw_read("alt_names"):
            lid = n.lg_id.strip()
            if lid in ids_lgs_ids:
                altnames[lid].append(n.name.strip())

        args.log.info("processing Glottolog data ...")
        glottolog_codes = self.glottolog.languoids_by_code()

        # get ISO language ID mapping
        _iso_codes = {lg.id.strip(): lg.sil_code.strip() for lg in self.ids_raw_read("sil_lang")}
        iso_codes = {
            lg.lg_id.strip(): _iso_codes[lg.sil_id.strip()] for lg in self.ids_raw_read("x_lg_sil")
        }

        lang_corrections = defaultdict(dict)
        for lg in dsv.reader(self.etc_dir / "languages.csv", dicts=True):
            if lg["lg_id"] in ids_lgs_ids:
                lang_corrections[lg["lg_id"]] = lg

        args.log.info("processing language data ...")
        for lg in ids_lgs:
            lg_id = lg.lg_id.strip()
            lang_changed = lang_corrections[lg_id]
            lg_name = lang_changed.get("name") or lg.lg_name
            iso = lang_changed.get("iso") or iso_codes.get(lg_id) or ""
            gl_ = ""
            if len(iso) > 3:
                gl_ = iso
                iso = ""
            gl = lang_changed.get("glottolog", gl_)
            if not gl and iso:
                gl = glottolog_codes[iso].id
            gl = GLOTTOCODE_UPDATES.get(gl, gl)
            date = lg.date.strip()
            if lg_id in edited_data:
                reprs = edited_data[lg_id]['reprs']
                date = edited_data[lg_id]['date']
            else:
                reprs = [data_desc[lg_id].get("1")]
                if data_desc[lg_id].get("2", ""):
                    if lg_id != "194":  # ignore 2. repr - it's in comment
                        reprs.append(data_desc[lg_id].get("2"))
            args.writer.add_language(
                ID=lg_id,
                Name=lg_name.strip(),
                Glottocode=gl,
                ISO639P3code=iso,
                Authors=personnel["2"][lg_id] or None,
                DataEntry=personnel["1"][lg_id] or None,
                Consultants=personnel["3"][lg_id] or None,
                Representations=reprs,
                Latitude=glottolog_codes[gl].latitude if gl else "",
                Longitude=glottolog_codes[gl].longitude if gl else "",
                alt_names=sorted(set(altnames[lg_id]) - {lg_name.strip()}) or "",
                date=date,
            )

        args.writer.objects["LanguageTable"] = sorted(
            args.writer.objects["LanguageTable"], key=lambda item: int(item["ID"])
        )

        problems = defaultdict(list)
        misaligned = []
        counterparts = set()
        wrds = defaultdict(int)

        etc_ids = defaultdict(lambda: defaultdict(list))
        corrected_rows_filename = self.etc_dir / "ids.all.csv"
        if corrected_rows_filename.exists():
            for lg in dsv.reader(corrected_rows_filename, namedtuples=True):
                if (
                    lg.lg_id in ids_lgs_ids
                    and "{0}-{1}".format(lg.chap_id, lg.entry_id) in entry_ids
                ):
                    etc_ids[lg.lg_id]["{0}-{1}".format(lg.chap_id, lg.entry_id)].append(lg)

        leave_org_values = list([703, 708, 709] + list(range(800, 813)) + list(range(814, 841)))

        args.log.info("grouping forms ...")
        for lg_id, entries in pylexibank.progressbar(
            groupby(sorted(self.ids_raw_read("ids"), key=lambda t: t.lg_id), lambda z: z.lg_id),
            desc="processing forms by languages",
        ):

            if not lg_id or lg_id not in ids_lgs_ids:
                continue

            desc = data_desc.get(lg_id, {})
            words = defaultdict(list)
            lg_org_value = defaultdict(str)
            entries_list = list(entries)

            # read forms of edited data as they are since they must be clean without any exceptions
            if lg_id in edited_data:
                for row in edited_data[lg_id]['data']:

                    entry_id = "{0}-{1}".format(row['Chapter'], row['Entry'])
                    if entry_id not in entry_ids:
                        continue
                    lg_entry_id = "{0}-{1}".format(lg_id, entry_id)
                    reprs = edited_data[lg_id]['reprs']
                    w = row[reprs[0]].strip()
                    if w and not empty.match(w):
                        w = unicodedata.normalize(self.form_spec.normalize_unicode, w)
                        alt_vals = []
                        for r in reprs[1:]:
                            alt_vals.append(row[r].strip())
                        args.writer.add_form(
                            Language_ID=lg_id,
                            Parameter_ID=entry_id,
                            Value=w,
                            Form=w,
                            Comment=row['Comment'].strip(),
                            Source=sources.get(lg.lg_id, ""),
                            Transcriptions=reprs,
                            AlternativeValues=alt_vals,
                        )
                continue

            # find last valid entry
            last_entry_idx = None
            for m, lg in enumerate(entries_list[::-1]):
                if (
                    empty.match(lg.data_1)
                    or "{0}-{1}".format(lg.chap_id, lg.entry_id) not in entry_ids
                ):
                    continue
                last_entry_idx = len(entries_list) - m - 1
                break

            for m, lg in enumerate(entries_list):

                if empty.match(lg.data_1):
                    continue

                entry_id = "{0}-{1}".format(lg.chap_id, lg.entry_id)
                if entry_id not in entry_ids:
                    continue

                lg_entry_id = "{0}-{1}".format(lg.lg_id, entry_id)

                if int(lg.lg_id) in leave_org_values:
                    lg_org_value[lg_entry_id] = lg.data_1
                elif not lg_org_value[lg_entry_id]:
                    lg_org_value[lg_entry_id] = lg.data_1

                # check for corrected data set
                if lg.lg_id in etc_ids and entry_id in etc_ids[lg.lg_id]:
                    if len(etc_ids[lg.lg_id][entry_id]) > 0:
                        lg = etc_ids[lg.lg_id][entry_id].pop(0)
                    else:
                        print(
                            "CHECK doublets of {0},{1},{2},".format(
                                lg.entry_id, lg.chap_id, lg.lg_id
                            )
                        )

                com = ""
                if lg.comment and not empty.match(lg.comment.strip()):
                    com = lg.comment.strip()

                lgdata_1 = lg.data_1
                # lg 318 makes additionally usage of | separators (in other lgs is it a click)
                if lg.lg_id == "318":
                    lgdata_1 = lgdata_1.replace(" || ", ";").replace(" | ", ";")

                trans1 = list(self.split_counterparts(lgdata_1))
                trans2 = (
                    None if empty.match(lg.data_2) else list(self.split_counterparts(lg.data_2))
                )
                if trans2:
                    if len(trans2) != len(trans1):
                        if lg_id == "238":
                            com = "{0} {1}".format(lg.data_2.strip(), com)
                        else:
                            misaligned.append((lg.chap_id, lg.entry_id, lg.lg_id))
                        trans2 = None

                for i, word in enumerate(trans1):
                    wrds[lg_entry_id] += 1
                    cid = "{0}-{1}".format(lg_entry_id, str(wrds[lg_entry_id]))

                    alt_val, alt_trans = "", ""
                    if trans2:
                        alt_val, com = self.preprocess_form_comment(
                            trans2[i], desc.get("2"), lg.lg_id, com, entry_id
                        )
                        alt_trans = desc.get("2", "").strip()
                        if alt_val and empty.match(alt_val):
                            alt_val, alt_trans = "", ""

                    w, com = self.preprocess_form_comment(
                        word, desc.get("1"), lg.lg_id, com, entry_id
                    )
                    if w and not empty.match(w):
                        if cid not in counterparts:
                            words[w].append((lg_entry_id, alt_val if alt_val else None))
                            counterparts.add(cid)
                        else:
                            print(cid)
                        reprs = [desc.get("1", "").strip()]
                        if alt_trans:
                            reprs.append(alt_trans)

                        if wrapped_in_brackets.search(w):
                            w = w[1:-1].strip()

                        if lg_id == "838":
                            # tone markers are wrapped in ()
                            w = re.sub(r"\((\d+)\)", "\\1", w)
                        if lg_id == "282":
                            # trailing ' [...]' is a pronunciation comment
                            w = re.sub(r"\s+\[[^]]+?]\s*$", "", w).strip()

                        w = self.form_spec.clean(w)
                        w = re.sub(r"-{2,}", "-", w)

                        if alt_val:
                            if wrapped_in_brackets.search(alt_val):
                                alt_val = alt_val[1:-1].strip()
                            alt_val = self.form_spec.clean(alt_val)

                        if w and not empty.match(w):
                            args.writer.add_form(
                                Language_ID=lg.lg_id,
                                Parameter_ID=entry_id,
                                Value=lg_org_value[lg_entry_id],
                                Form=unicodedata.normalize(self.form_spec.normalize_unicode, w),
                                Comment=com,
                                Source=sources.get(lg.lg_id, ""),
                                Transcriptions=reprs,
                                AlternativeValues=[alt_val],
                            )

                # add possible remaining corrected entries (mostly splitted ones)
                if m == last_entry_idx:
                    for k, v in etc_ids[lg.lg_id].items():
                        if len(v) > 0:
                            entries_list.extend(v)

            for i, form in enumerate(words.keys()):
                alt_names = [] if lg_id == "238" else set(w[1] or "" for w in words[form])
                alt_ids = set(w[0] or "" for w in words[form])
                alt_id = alt_ids.pop() if len(alt_ids) else ""
                alt_names = nfilter(alt_names)
                try:
                    assert len(alt_names) <= 1
                except AssertionError:
                    problems[(lg_id, alt_id)].append(alt_names)

        print()
        if len(problems):
            print("=== Problems ===")
            for k, v in problems.items():
                print(k, v)
        print()
        if len(misaligned):
            print("=== Misaligned ===")
            for k in misaligned:
                print(k)

        # sort FormTable
        def _x(s):
            to_sort = s.split("-")
            return int(to_sort[0]), int(to_sort[1]), int(to_sort[2]), int(to_sort[3])

        args.writer.objects["FormTable"] = sorted(
            args.writer.objects["FormTable"], key=lambda z: _x(z["ID"])
        )

        self.apply_cldf_defaults(args)
