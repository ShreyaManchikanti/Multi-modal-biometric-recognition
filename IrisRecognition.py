import numpy as np
import Iris__gabor_module as ir
from sklearn.metrics.pairwise import cosine_similarity

# Load known iris data
known_iris = np.load('files1/known_iris.npy', allow_pickle=True)
known_iris_names = np.load('files1/known_iris_names.npy', allow_pickle=True)

def recognize_iris(new_iris_image_path):
    try:
        # Load the new iris image
        new_iris_image = ir.load_image_file(new_iris_image_path)

        # Encode the new iris image
        new_code, new_mask = ir.encode_iris(new_iris_image)

        # Initialize variables to track the best match
        best_match_index = None
        best_match_distance = 0

        # Compare the new iris encoding with known iris encodings
        for i, (known_code, known_mask) in enumerate(known_iris):
            # Calculate the distance between the new iris code and the known iris code
            distance = np.sum((known_code - new_code)**2)
            # print("***********",distance)

            # Check if this is the best match so far
            if distance == best_match_distance:
                best_match_distance = distance
                best_match_index = i

        # If a match is found, return the corresponding name
        if best_match_index is not None:
            return known_iris_names[best_match_index]
        else:
            return "iris not recognized"

    except Exception as e:
        print("Error in recognizing iris", e)
        return "Error in recognizing iris"

# Example usage
new_iris_image_path = 'iris\Sarina\sarinal2.bmp'
recognized_name = recognize_iris(new_iris_image_path)
print("Recognized iris:", recognized_name)