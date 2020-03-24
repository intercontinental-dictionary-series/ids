import attr
from clldutils.path import Path
from pylexibank import Lexeme
from pylexibank.forms import FormSpec
from pylexibank.providers import clld
from pylexibank.util import progressbar

# Import for local segmentation
import unicodedata
from segments import Tokenizer, Profile
from segments.tree import Tree

GLOTTOCODE_UPDATES = {
    "sana1281": "sana1298",
    "pray1239": "phai1238",
    "samr1245": "somr1240",
}


@attr.s
class CustomLexeme(Lexeme):
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
    lexeme_class = CustomLexeme

    def cmd_makecldf(self, args):
        # parse concepts
        ccode = {
            x.attributes["ids_id"]: x.concepticon_id
            for x in self.conceptlists[0].concepts.values()
        }

        args.writer.add_sources()

        # write languges
        for row in self.original_cldf["LanguageTable"]:
            args.writer.add_language(
                ID=row["ID"],
                Name=row["Name"],
                Glottocode=GLOTTOCODE_UPDATES.get(
                    row["Glottocode"], row["Glottocode"]
                ),
            )

        # write concepts
        for row in self.original_cldf["ParameterTable"]:
            args.writer.add_concept(
                ID=row["ID"],
                Name=row.pop("Name"),
                Concepticon_ID=ccode[row["ID"]],
            )

        # locally load tokenizers; when issue #197 on pylexibank, it might
        # be removed (but consider the individual language profiles, such
        # as for Pano languages)
        def get_tokenizer(profile_):
            profile_ = Profile.from_file(str(profile_), form="NFC")
            default_spec = list(next(iter(profile_.graphemes.values())).keys())
            for grapheme in ["^", "$"]:
                if grapheme not in profile_.graphemes:
                    profile_.graphemes[grapheme] = {
                        k: None for k in default_spec
                    }
            profile_.tree = Tree(list(profile_.graphemes.keys()))
            return Tokenizer(
                profile=profile_, errors_replace=lambda c: "<{0}>".format(c)
            )

        def apply_tokenizer(form, tokenizer):
            return tokenizer(unicodedata.normalize("NFC", form)).split()

        tokenizers = {}
        profile_dir = self.etc_dir / "profiles"
        for profile in profile_dir.glob("*.tsv"):
            tokenizers[profile.stem] = get_tokenizer(profile)

        # Iterate over rows
        for row in progressbar(self.original_cldf["FormTable"]):
            row["Value"] = row.pop("Form")
            row["Language_ID"] = row.pop("Language_ID")
            row["Parameter_ID"] = row.pop("Parameter_ID")
            row["AlternativeValue"] = row.pop("alt_form")
            row["Transcription"] = (row.pop("transcription") or "").lower()
            row["AlternativeTranscription"] = (
                row.pop("alt_transcription") or ""
            ).lower()
            del row["ID"]
            del row["Contribution_ID"]

            # Default to `phonemic` transcription
            if (
                row["AlternativeTranscription"] == "phonemic"
                and row["AlternativeValue"]
            ):
                value = row["AlternativeValue"]
                transcription = row["AlternativeTranscription"]
            else:
                value = row["Value"]
                transcription = row["Transcription"]

            # Add forms
            for i, form in enumerate(self.form_spec.split({}, value, {})):
                if transcription in tokenizers:
                    segments = apply_tokenizer(form, tokenizers[transcription])
                else:
                    segments = [c for c in form]

                # TODO: temporary for development
                if transcription != "phonemic":
                    segments = ["a"]

                # Add forms
                args.writer.add_form_with_segments(
                    Language_ID=row["Language_ID"],
                    Parameter_ID=row["Parameter_ID"],
                    Value=row["Value"],
                    Form=form,
                    Source=row["Source"],
                    AlternativeValue=row["AlternativeValue"],
                    Transcription=row["Transcription"],
                    AlternativeTranscription=row["AlternativeTranscription"],
                    Segments=segments,
                )
