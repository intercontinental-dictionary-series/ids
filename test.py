def test_valid(cldf_dataset, cldf_logger):
    assert cldf_dataset.validate(log=cldf_logger)


def test_forms(cldf_dataset):
    assert len(list(cldf_dataset["FormTable"])) == 437902
    assert any(f["Form"] == "гІемерцІул" for f in cldf_dataset["FormTable"])
    assert any(f["Form"] == "сгæллад" for f in cldf_dataset["FormTable"])


def test_parameters(cldf_sqlite_database):
    assert cldf_sqlite_database.query("select count(*) from ParameterTable")[0][0] == 1310


def test_languages(cldf_dataset):
    assert len(list(cldf_dataset["LanguageTable"])) == 319

