import attr
from clldutils.path import Path
from clldutils.text import strip_chars, split_text_with_context
from pylexibank.dataset import Lexeme, Language
from pylexibank.providers import clld

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
    date = attr.ib(default=None)

class Dataset(clld.CLLD):
    __cldf_url__ = "http://cdstar.shh.mpg.de/bitstreams/EAEA0-5F01-8AAF-CDED-0/ids_dataset.cldf.zip"

    dir = Path(__file__).parent
    id = "ids"
    lexeme_class = IDSLexeme
    language_class = IDSLanguage

    def split_forms(self, row, value):
        value = self.lexemes.get(value, value)
        return filter(None,[
            self.clean_form(row, form) for form in split_text_with_context(value, separators="/,;~")
        ])

    def clean_form(self, item, form):
        form = strip_chars("[]()*^?=", form)
        if form and strip_chars("- ", form) not in ["\u2014", "?", "???", "", "666"]:
            return form

    def cmd_install(self, **kw):
        ccode = {
            x.attributes["ids_id"]: x.concepticon_id for x in self.conceptlist.concepts.values()
        }
        glottolog_codes = self.glottolog.languoids_by_code()

        sep = self.original_cldf.__getitem__(('contributions.csv', 'Contributors')).separator
        contributors = {}
        for i, row in enumerate(self.raw.read_csv('contributions.csv')):
            if i:
                contributors[row[0]] = row[3].split(sep)


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
                row["Value"] = row.pop("Form")
                row["AlternativeValue"] = row.pop("alt_form")
                row["Transcription"] = (row.pop("transcription") or "").lower()
                row["AlternativeTranscription"] = (row.pop("alt_transcription") or "").lower()
                del row["ID"]
                del row["Contribution_ID"]
                del row["Segments"]
                ds.add_lexemes(**row)

            ds.objects['LanguageTable'] = sorted(ds.objects['LanguageTable'],
                    key=lambda item: int(item['ID']))

            ds.wl['LanguageTable', 'Contributors'].separator = sep
