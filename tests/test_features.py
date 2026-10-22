import pytest

from phishlens.features import COLUMNS, describe, entropy, name_features


def test_brand_on_its_own_and_borrowed():
    assert name_features("paypal")["brand_exact"] == 1 and name_features("paypal")["brand_inside"] == 0
    assert name_features("paypal-login")["brand_exact"] == 0 and name_features("paypal-login")["brand_inside"] == 1


def test_counts():
    f = name_features("secure-login-2024", "co.uk")
    assert (f["digits"], f["hyphens"], f["action_words"], f["suffix_levels"]) == (4, 2, 2, 2)
    assert f["length"] == 17


def test_entropy():
    assert entropy("aaaa") == 0
    assert entropy("abcd") == pytest.approx(2.0)


def test_every_feature_can_be_described():
    f = name_features("xn--pypal-4ve", "com")
    f.update(suffix="com", name_pattern=0.9)
    for column in COLUMNS:
        assert isinstance(describe(column, f[column], "xn--pypal-4ve", "com"), str)
