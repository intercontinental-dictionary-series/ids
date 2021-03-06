from setuptools import setup
import json


with open("metadata.json", encoding="utf-8") as fp:
    metadata = json.load(fp)


setup(
    name="lexibank_ids",
    description=metadata["title"],
    license=metadata["license"],
    url=metadata["url"],
    py_modules=["lexibank_ids"],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "lexibank.dataset": [
            "ids=lexibank_ids:Dataset"
        ]
    },
    install_requires=[
        "pylexibank>=2.7.1",
        "clldutils>=3.5.2",
        "csvw>=1.8.0",
        "idspy>=0.2",
    ],
    extras_require={
        "test": [
            "pytest-cldf"
        ]
    },
)
