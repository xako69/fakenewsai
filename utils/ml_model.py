import pickle

try:
    model = pickle.load(open("models/ml_model.pkl", "rb"))
except:
    model = None

def predict_ml(text):
    if model is None:
        return "UNKNOWN", 0

    prob = model.predict_proba([text])[0]
    label = model.predict([text])[0]

    confidence = round(max(prob) * 100, 2)

    return label, confidence