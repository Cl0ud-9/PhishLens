"""How much a name's letter patterns resemble phishing names: logistic regression on character n-grams."""
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression

# Hashing keeps no vocabulary, so the model is just one weight per hash bucket, saved as a plain array
VECTORIZER = HashingVectorizer(analyzer="char_wb", ngram_range=(2, 5), n_features=2**18, alternate_sign=False,
                               norm="l2")


class NamePattern:
    def __init__(self, coef, intercept):
        self.coef = np.asarray(coef, dtype=np.float64)
        self.intercept = float(intercept)

    @classmethod
    def fit(cls, names, labels, c=4.0):
        model = LogisticRegression(C=c, max_iter=3000).fit(VECTORIZER.transform(names), labels)
        return cls(model.coef_[0], model.intercept_[0])

    def score(self, names):
        """Probability-like score from 0 (looks like genuine names) to 1 (looks like phishing names)."""
        z = VECTORIZER.transform(list(names)) @ self.coef + self.intercept
        return 1.0 / (1.0 + np.exp(-z))
