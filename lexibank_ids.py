import attr
from clldutils.path import Path
from pylexibank import Lexeme
from pylexibank.forms import FormSpec
from pylexibank.providers import clld
from pylexibank.util import progressbar

GLOTTOCODE_UPDATES = {"sana1281": "sana1298", "pray1239": "phai1238", "samr1245": "somr1240"}


@attr.s
class IDSLexeme(Lexeme):
    Transcription = attr.ib(default=None)
    AlternativeValue = attr.ib(default=None)
    AlternativeTranscription = attr.ib(default=None)


class Dataset(clld.CLLD):
    form_spec = FormSpec(
        brackets={"(": ")", "[": "]"},
        replacements=[("[", ""), ("]", ""), ("(", ""), (")", "")],
        separators="/,;~",
        missing_data=("-", "--", "\u2014", "?", "???", "", "-)"),
        strip_inside_brackets=False,
    )

    __cldf_url__ = "http://cdstar.shh.mpg.de/bitstreams/EAEA0-5F01-8AAF-CDED-0/ids_dataset.cldf.zip"

    dir = Path(__file__).parent
    id = "ids"
    lexeme_class = IDSLexeme

    def cmd_makecldf(self, args):
        ccode = {
            x.attributes["ids_id"]: x.concepticon_id for x in self.conceptlist.concepts.values()
        }

        args.writer.add_sources()

        for row in self.original_cldf["LanguageTable"]:
            args.writer.add_language(
                ID=row["ID"],
                Name=row["Name"],
                Glottocode=GLOTTOCODE_UPDATES.get(row["Glottocode"], row["Glottocode"]),
            )

        for row in self.original_cldf["ParameterTable"]:
            args.writer.add_concept(
                ID=row["ID"], Name=row.pop("Name"), Concepticon_ID=ccode[row["ID"]]
            )

        for row in progressbar(self.original_cldf["FormTable"]):
            row["Value"] = row.pop("Form")
            row["Language_ID"] = row.pop("Language_ID")
            row["Parameter_ID"] = row.pop("Parameter_ID")
            row["AlternativeValue"] = row.pop("alt_form")
            row["Transcription"] = (row.pop("transcription") or "").lower()
            row["AlternativeTranscription"] = (row.pop("alt_transcription") or "").lower()
            del row["ID"]
            del row["Contribution_ID"]
            args.writer.add_forms_from_value(
                Language_ID=row["Language_ID"],
                Parameter_ID=row["Parameter_ID"],
                Value=row["Value"],
                Source=row["Source"],
                AlternativeValue=row["AlternativeValue"],
                Transcription=row["Transcription"],
                AlternativeTranscription=row["AlternativeTranscription"],
            )
