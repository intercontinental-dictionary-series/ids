from setuptools import setup
import sys
import json


PY2 = sys.version_info.major == 2
with open('metadata.json', **({} if PY2 else {'encoding': 'utf-8'})) as fp:
    metadata = json.load(fp)


setup(
    name='lexibank_ids',
    description=metadata['title'],
    license=metadata['license'],
    url=metadata['url'],
    py_modules=['lexibank_ids'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'lexibank.dataset': [
            'ids=lexibank_ids:Dataset',
        ]
    },
    install_requires=[
        'pylexibank',
    ]
)
