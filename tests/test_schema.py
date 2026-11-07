import pandas as pd

from core.validation import FEATURE_COLUMNS, validate_columns, validate_ranges


def test_validate_columns_success():
    df = pd.DataFrame([{col: 1 for col in FEATURE_COLUMNS}])
    validate_columns(df)


def test_validate_columns_missing_raises():
    df = pd.DataFrame([{"age": 60}])
    try:
        validate_columns(df)
    except ValueError as ex:
        assert "Missing required columns" in str(ex)
        return
    assert False, "Expected ValueError for missing columns"


def test_validate_ranges_flags_outliers():
    row = {col: 1 for col in FEATURE_COLUMNS}
    row.update({"age": 180, "eGFR": -1})
    df = pd.DataFrame([row])
    issues = validate_ranges(df)
    assert any("age" in x for x in issues)
    assert any("eGFR" in x for x in issues)
