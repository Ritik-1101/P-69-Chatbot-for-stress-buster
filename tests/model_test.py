# tests/test_model.py

from model import train_model

def test_model_accuracy():
    model, accuracy = train_model()
    assert accuracy >= 0.8  # Expect the model to have at least 80% accuracy

def test_model_not_none():
    model, accuracy = train_model()
    assert model is not None  # Ensure that the model is not None

def test_model_accuracy_failure():
    model, accuracy = train_model()
    assert accuracy >= 0.95  # This test will fail if accuracy is below 95%
