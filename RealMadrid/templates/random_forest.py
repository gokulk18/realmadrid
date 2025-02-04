import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import joblib  # Import joblib for saving the model

# Model path for testing
model_path = "D:\\realmadrid\\RealMadrid\\templates\\fitness_stats.csv"  # Update with the model path

# Load the dataset
data = pd.read_csv(model_path)

# Check for missing values and handle them (example: drop rows with missing values)
data.dropna(inplace=True)

# Assuming 'Match Fit' is the target variable and 'Player Name' should be excluded
X = data.drop(columns=['Player Name', 'Match Fit'])  # Features

# One-hot encode categorical features if any (including 'Injury Status')
X = pd.get_dummies(X, drop_first=True)

# Save feature names
feature_names = X.columns.tolist()  # Get the feature names
with open("feature_names.txt", "w") as f:  # Save to a text file
    for name in feature_names:
        f.write(f"{name}\n")

# Encode the target variable if it's categorical
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(data['Match Fit'])

# Split the dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the Random Forest model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)  # Make predictions on the test set
accuracy = accuracy_score(y_test, y_pred)  # Calculate accuracy
print(f"Model accuracy: {accuracy:.2f}")  # Print the accuracy

# Calculate confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)  # Get the confusion matrix
TP = conf_matrix[1, 1]  # True Positives
TN = conf_matrix[0, 0]  # True Negatives
FP = conf_matrix[0, 1]  # False Positives
FN = conf_matrix[1, 0]  # False Negatives

# Print the confusion matrix values
print(f"True Positives: {TP}, True Negatives: {TN}, False Positives: {FP}, False Negatives: {FN}")

# Save the trained model to a file
model_filename = "random_forest_model.joblib"  # Specify the filename
joblib.dump(model, model_filename)  # Save the model

print(f"Model saved to {model_filename}")
