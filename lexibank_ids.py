# coding: utf8
from __future__ import unicode_literals, print_function, division

import attr
from unidecode import unidecode
from lingpy.sequence.sound_classes import ipa2tokens
from clldutils.path import Path, as_unicode
from clldutils.text import strip_chars, split_text_with_context
from clldutils.jsonlib import load
from clldutils.misc import lazyproperty

from pylexibank.providers import clld
from pylexibank.dataset import Metadata, Lexeme


@attr.s
class IDSLexeme(Lexeme):
    Transcription = attr.ib(default=None)
    AlternativeValue = attr.ib(default=None)
    AlternativeTranscription = attr.ib(default=None)


class Dataset(clld.CLLD):
    __cldf_url__ = "http://cdstar.shh.mpg.de/bitstreams/EAEA0-5F01-8AAF-CDED-0/ids_dataset.cldf.zip"

    dir = Path(__file__).parent
    lexeme_class = IDSLexeme
    
    def split_forms(self, row, value):
        value = self.lexemes.get(value, value)
        return [self.clean_form(row, form)
                for form in split_text_with_context(value, separators='/,;~')]

    def clean_form(self, item, form):
        chars2strip = '[]()*='
        if item['Transcription'] in ['phonemic', 'phonetic', 'latintrans']:
            form = clld.CLLD.clean_form(self, item, strip_chars(
                chars2strip, form))
        elif item['Transcription'] == 'cyrilltrans':
            if item['AlternativeTranscription'] in ['phonemic', 'phonetic'] and \
                    item['AlternativeValue']:
                form = clld.CLLD.clean_form(self, item, strip_chars(
                    chars2strip, item['AlternativeValue']))
            else:
                form = clld.CLLD.clean_form(self, item, strip_chars(
                    chars2strip, unidecode(form).lower()))
        else:
            form = None
        if form and strip_chars('- ', form) not in ['\u2014', '?', '???', '']:
            return form

    @lazyproperty
    def tokenizer(self):
        return lambda _, string: ipa2tokens(
            string.replace(' ', '_'),
            semi_diacritics='szh',
            merge_vowels=False)

    def cmd_install(self, **kw):
        ccode = {x.attributes['ids_id']: x.concepticon_id for x in
                 self.conceptlist.concepts.values()}

        with self.cldf as ds:
            self.add_sources(ds)

            for row in self.original_cldf['LanguageTable']:
                ds.add_language(
                    ID=row['ID'],
                    Name=row['Name'],
                    Glottocode=row['Glottocode'])

            for row in self.original_cldf['ParameterTable']:
                ds.add_concept(
                    ID=row['ID'],
                    Name=row.pop('Name'),
                    Concepticon_ID=ccode[row['ID']])

            for row in self.original_cldf['FormTable']:
                row['Value'] = row.pop('Form')
                row['AlternativeValue'] = row.pop('alt_form')
                row['Transcription'] = (row.pop('transcription') or '').lower()
                row['AlternativeTranscription'] = (row.pop('alt_transcription') or '').lower()
                del row['ID']
                del row['Contribution_ID']
                ds.add_lexemes(**row)
