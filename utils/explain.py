import numpy as np
from lime.lime_text import LimeTextExplainer

class_names = ["FAKE", "REAL"]

def lime_explanation(text, model, vectorizer, num_features=10):
    """
    Generates top influential words using LIME.
    Returns list of (word, weight)
    """

    def predict_proba(texts):
        X = vectorizer.transform(texts)
        return model.predict_proba(X)

    explainer = LimeTextExplainer(class_names=class_names)
    exp = explainer.explain_instance(
        text,
        predict_proba,
        num_features=num_features
    )
    return exp.as_list()
