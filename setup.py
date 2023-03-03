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
        "cldfbench>=1.13.0",
        "pylexibank>=3.4.0",
        "clldutils>=3.19.0",
        "csvw>=3.1.3",
        "idspy>=0.3.0",
    ],
    extras_require={
        "test": [
            "pytest-cldf"
        ]
    },
)
