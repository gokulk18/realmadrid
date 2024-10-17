import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# Model path for testing
model_path = "D:\\realmadrid\\RealMadrid\\templates\\fitness_stats.csv"  # Update with the model path

# Load the dataset
data = pd.read_csv(model_path)

# Check for missing values and handle them (example: drop rows with missing values)
data.dropna(inplace=True)

# Assuming 'Match Fit' is the target variable and 'Player Name' should be excluded
X = data.drop(columns=['Player Name', 'Match Fit'])  # Features
y = data['Match Fit']  # Target variable

# One-hot encode categorical features if any (excluding 'Player Nar')
X = pd.get_dummies(X, drop_first=True)

# Encode the target variable if it's categorical
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y)

# Split the dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier()
model.fit(X_train, y_train)

# Example input for predicting match fit (replace with actual values)
# Ensure the input matches the feature set used for training
test_input = [[9.4, 7.8, 135, 0, 290, 48, 85, 8]]  # Example input

# Make prediction
predicted_fit = model.predict(test_input)

# Convert numerical prediction back to categorical label
predicted_label = label_encoder.inverse_transform(predicted_fit)

print("Predicted Match Fit Status:", predicted_label[0])  # Output the prediction