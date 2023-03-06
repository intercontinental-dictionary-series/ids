# Releasing IDS CLDF dataset


## Preparations

- Make sure you have set all desired changes and publishing dates
- Run
  ```
  cldfbench lexibank.makecldf --concepticon {PATH} ./lexibank_ids.py
  ```
- Make sure .zenodo.json and cldf/README.md are present and up-to-date
    - if not run
    ```
    cldfbench zenodo ./lexibank_ids.py
    cldfbench cldfreadme ./lexibank_ids.py
    ```
- Commit everything to `master` (as PR)

## Create new release

- go to [https://github.com/intercontinental-dictionary-series/ids/releases](https://github.com/intercontinental-dictionary-series/ids/releases) and draft a new release
- choose a new tag and press the `+` button
- fill out all required fields (can be taken over from latest release with relevant changes)
- make sure that `Set as the latest release` is checked
- choose `Publish release` that not only creates a new release but also initiates the publication at Zenodo
- wait a moment and look at [https://doi.org/10.5281/zenodo.1299512]() if the new release is listed; if so copy the new DOI number
- go back to [https://github.com/intercontinental-dictionary-series/ids/releases](https://github.com/intercontinental-dictionary-series/ids/releases) and update the new DOI number of the latest release version
