import math

import numpy as np
import pytest

from phishlens import PhishLens, check
from phishlens.check import HIGH, LOW


@pytest.fixture(scope="module")
def model():
    return PhishLens.load()


def test_obvious_phishing_is_high_risk(model):
    v = check("https://paypal-secure-login-verify.com/signin", model)
    assert v.level == "high" and v.score >= HIGH


def test_a_plain_genuine_domain_is_low_risk(model):
    v = check("https://www.viit.ac.in", model)
    assert v.level == "low" and v.score < LOW


def test_shap_values_add_up_to_the_score(model):
    frame = model.frame(["dhl-delivery-update"], ["info"])
    contrib = model.contributions(frame)[0]
    p = model.score(frame)[0]
    assert contrib.sum() == pytest.approx(math.log(p / (1 - p)), abs=1e-6)


def test_save_and_load_give_the_same_scores(model, tmp_path):
    model.save(tmp_path)
    again = PhishLens.load(tmp_path)
    frame = model.frame(["example", "secure-verify-2024"], ["com", "top"])
    assert np.allclose(model.score(frame), again.score(again.frame(["example", "secure-verify-2024"], ["com", "top"])))


def test_a_model_with_other_features_is_refused(model, tmp_path):
    model.save(tmp_path)
    meta = tmp_path / "phishlens.json"
    meta.write_text(meta.read_text().replace('"name_pattern"', '"something_else"'))
    with pytest.raises(ValueError):
        PhishLens.load(tmp_path)
