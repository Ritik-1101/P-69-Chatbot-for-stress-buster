
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

def train_model():
    iris = load_iris()
    X = iris.data
    y = (iris.target == 0).astype(int) 

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LogisticRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    
    return model, accuracy

if __name__ == "__main__":
    model, accuracy = train_model()
    print(f"Model accuracy: {accuracy:.2f}")
