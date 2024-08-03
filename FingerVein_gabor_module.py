import cv2
import numpy as np
from skimage.util import view_as_blocks
import matplotlib.pyplot as plt

def preprocess_finger_vein(image):
    """Preprocess the finger vein image to enhance the vein patterns."""
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
    return blur_image

def gabor_filter(image, frequency, theta):
    """Apply Gabor filter to the image to extract vein patterns."""
    kernel = cv2.getGaborKernel((21, 21), 4.0, theta, frequency, 0.5, 0, ktype=cv2.CV_32F)
    filtered_image = cv2.filter2D(image, cv2.CV_8UC3, kernel)
    return filtered_image

def encode_finger_vein(image, block_size=(16, 16)):
    """Encode the finger vein image into a binary code."""
    preprocessed_image = preprocess_finger_vein(image)
    frequency = 0.1  # Frequency for Gabor filter
    angles = [0, np.pi/4, np.pi/2, 3*np.pi/4]  # Different angles for Gabor filters

    codes = []
    masks = []

    for theta in angles:
        filtered_image = gabor_filter(preprocessed_image, frequency, theta)
        blocks = view_as_blocks(filtered_image, block_size)
        code = np.zeros((blocks.shape[0], blocks.shape[1]), dtype=int)
        mask = np.zeros((blocks.shape[0], blocks.shape[1]), dtype=int)

        for i in range(blocks.shape[0]):
            for j in range(blocks.shape[1]):
                block = blocks[i, j]
                mean_intensity = np.mean(block)
                # print("**********",mean_intensity)
                code[i, j] = 1 if mean_intensity > 157 else 0
                mask[i, j] = 1

        codes.append(code)
        masks.append(mask)

    final_code = np.concatenate(codes, axis=1)
    final_mask = np.concatenate(masks, axis=1)
    
    return final_code, final_mask

def load_image_file(filepath):
    """Load an image file."""
    return cv2.imread(filepath)

def visualize_final_image(image_path):
    image = load_image_file(image_path)
    code, mask = encode_finger_vein(image)

    # plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.title("Final Encoded Iris Image")
    plt.imshow(code, cmap='gray')
    plt.subplot(1, 2, 2)
    plt.title("Mask")
    plt.imshow(mask, cmap='gray')
    plt.show()

if __name__ == "__main__":
    # Example usage
    image_path = 'FingerVein/Keerti/Keerti_1.bmp'
    visualize_final_image(image_path)