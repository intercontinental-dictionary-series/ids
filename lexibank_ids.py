import attr
from clldutils.path import Path
from pylexibank.dataset import Lexeme, Language
from pylexibank.providers import clld
import unicodedata

GLOTTOCODE_UPDATES = {"sana1281": "sana1298", "pray1239": "phai1238", "samr1245": "somr1240"}


@attr.s
class IDSLexeme(Lexeme):
    Transcription = attr.ib(default=None)
    AlternativeValue = attr.ib(default=None)
    AlternativeTranscription = attr.ib(default=None)


@attr.s
class IDSLanguage(Language):
    Contributors = attr.ib(default=None)
    default_representation = attr.ib(default=None)
    alt_representation = attr.ib(default=None)
    alt_names = attr.ib(default=None)
    date = attr.ib(default=None)

class Dataset(clld.CLLD):
    __cldf_url__ = "http://cdstar.shh.mpg.de/bitstreams/EAEA0-5F01-8AAF-CDED-0/ids_dataset.cldf.zip"

    dir = Path(__file__).parent
    id = "ids"
    lexeme_class = IDSLexeme
    language_class = IDSLanguage

    strip_inside_brackets = False
    missing_data = ('?', '-', '???', '', '666', '\u2014')

    def cmd_install(self, **kw):
        ccode = {
            x.attributes["ids_id"]: x.concepticon_id for x in self.conceptlist.concepts.values()
        }
        glottolog_codes = self.glottolog.languoids_by_code()

        sep_ctr = self.original_cldf.__getitem__(('contributions.csv', 'Contributors')).separator
        sep_alt_n = self.original_cldf.__getitem__(('languages.csv', 'alt_names')).separator
        contributors = {}
        for i, row in enumerate(self.raw.read_csv('contributions.csv')):
            if i:
                contributors[row[0]] = row[3].split(sep_ctr)


        with self.cldf as ds:

            self.add_sources(ds)

            # add chapters.csv to cldf
            ds.wl.add_component(dict(
                url='chapters.csv',
                tableSchema=dict(columns=[
                    dict(name='ID', datatype='string', required=True),
                    dict(name='Description', datatype='string'),
                ])
            ))
            ds.write(**{'chapters.csv': self.original_cldf['chapters.csv']})

            for row in self.original_cldf["LanguageTable"]:
                gc = GLOTTOCODE_UPDATES.get(row["Glottocode"], row["Glottocode"])
                try:
                    iso = glottolog_codes[gc].iso
                except:
                    iso = ''
                dr, ar = None, None
                if row["representations"]:
                    dr = row["representations"][0]
                    if len(row["representations"]) > 1:
                        ar = row["representations"][1]
                ds.add_language(
                    ID=row["ID"],
                    Name=row["Name"],
                    Glottocode=gc,
                    ISO639P3code=iso,
                    Contributors=contributors[row["ID"]],
                    default_representation=dr,
                    alt_representation=ar,
                    alt_names=row["alt_names"],
                    date=row["date"],
                )
                ds.objects['LanguageTable'][-1]['Latitude'] = row['Latitude']
                ds.objects['LanguageTable'][-1]['Longitude'] = row['Longitude']

            for row in self.original_cldf["ParameterTable"]:
                ds.add_concept(
                    ID=row["ID"],
                    Name=row.pop("Name"),
                    Concepticon_ID=ccode[row["ID"]]
                )

            for row in self.original_cldf["FormTable"]:
                av = row.pop("alt_form")
                if av:
                    av = unicodedata.normalize('NFC', av)
                row["Value"] = unicodedata.normalize('NFC', row.pop("Form"))
                row["AlternativeValue"] = av
                row["Transcription"] = row.pop("transcription") or ""
                row["AlternativeTranscription"] = row.pop("alt_transcription") or ""
                del row["ID"]
                del row["Contribution_ID"]
                del row["Segments"]
                ds.add_forms_from_value(**row)

            ds.objects['LanguageTable'] = sorted(ds.objects['LanguageTable'],
                    key=lambda item: int(item['ID']))

            ds.wl['LanguageTable', 'Contributors'].separator = sep_ctr
            ds.wl['LanguageTable', 'alt_names'].separator = sep_alt_n
