# model.py

from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

def train_model():
    # Load the Iris dataset
    iris = load_iris()
    X = iris.data
    y = (iris.target == 0).astype(int)  # Binary classification: Iris-Setosa vs. not

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the Logistic Regression model
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Make predictions on the test set
    y_pred = model.predict(X_test)

    # Calculate the accuracy of the model
    accuracy = accuracy_score(y_test, y_pred)
    
    return model, accuracy

if __name__ == "__main__":
    model, accuracy = train_model()
    print(f"Model accuracy: {accuracy:.2f}")
