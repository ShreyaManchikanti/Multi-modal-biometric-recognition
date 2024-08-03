from scipy.spatial.distance import euclidean
import warnings
warnings.filterwarnings('ignore')

def calculate_euclidean_distance(code1, code2):
    return euclidean(code1.flatten(), code2.flatten())

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

# Load known FingerVein data
known_FingerVein = np.load('files1/known_FingerVein.npy', allow_pickle=True)
known_FingerVein_names = np.load('files1/known_FingerVein_names.npy', allow_pickle=True)

# Split data into train and validation sets
X_train, X_val, y_train, y_val = train_test_split(known_FingerVein, known_FingerVein_names, test_size=0.2, random_state=42)

def evaluate_distance_metric(distance_metric):
    y_pred = []
    for val_code, val_mask in X_val:
        best_match_index = None
        best_match_distance = float('inf')
        
        for i, (train_code, train_mask) in enumerate(X_train):
            if train_code.shape != val_code.shape:
                continue
            distance = distance_metric(train_code, val_code)
            if distance < best_match_distance:
                best_match_distance = distance
                best_match_index = i
        
        if best_match_index is not None:
            y_pred.append(y_train[best_match_index])
        else:
            y_pred.append("Unknown")

    accuracy = accuracy_score(y_val, y_pred)
    f1 = f1_score(y_val, y_pred, average='weighted')
    
    return accuracy, f1

accuracy, f1 = evaluate_distance_metric(calculate_euclidean_distance)
print(f"Euclidean - Accuracy: {accuracy}")
print(f"Euclidean - F1 Score: {f1}")
