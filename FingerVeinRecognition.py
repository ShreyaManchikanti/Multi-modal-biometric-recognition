import numpy as np
import FingerVein_gabor_module as fv

# Load known finger_vein data
known_finger_vein = np.load('files1/known_FingerVein.npy', allow_pickle=True)
known_finger_vein_names = np.load('files1/known_FingerVein_names.npy', allow_pickle=True)

def recognize_finger_vein(new_finger_vein_image_path):
    try:
        # Load the new finger_vein image
        new_finger_vein_image = fv.load_image_file(new_finger_vein_image_path)

        # Encode the new finger_vein image
        new_code, new_mask = fv.encode_finger_vein(new_finger_vein_image)

        # Initialize variables to track the best match
        best_match_index = None
        best_match_distance = 0

        # Compare the new finger_vein encoding with known finger_vein encodings
        for i, (known_code, known_mask) in enumerate(known_finger_vein):
            # Calculate the distance between the new finger_vein code and the known finger_vein code
            distance = np.sum((known_code - new_code)**2)
            # print("***********",distance)

            # Check if this is the best match so far
            if distance == best_match_distance:
                best_match_distance = distance
                best_match_index = i

        # If a match is found, return the corresponding name
        if best_match_index is not None:
            return known_finger_vein_names[best_match_index]
        else:
            return "finger_vein not recognized"

    except Exception as e:
        print("Error in recognizing finger_vein", e)
        return "Error in recognizing finger_vein"

# Example usage
new_finger_vein_image_path = 'Test Fingervein images\Fiza_1.bmp'
recognized_name = recognize_finger_vein(new_finger_vein_image_path)
print("Recognized finger_vein:", recognized_name)
