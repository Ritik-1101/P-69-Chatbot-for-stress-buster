# tests/test_model.py

from model import train_model

def test_model_accuracy():
    model, accuracy = train_model()
    assert accuracy >= 0.8 

def test_model_not_none():
    model, accuracy = train_model()
    assert model is not None  

def test_model_accuracy_failure():
    model, accuracy = train_model()
    assert accuracy >= 0.95 
