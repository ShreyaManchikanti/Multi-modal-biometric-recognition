# Dataset link : https://www.kaggle.com/datasets/ryeltsin/finger-vein

from cv2 import threshold
import FingerVein_gabor_module as fv
import numpy as np
import os

known_finger_vein, known_finger_vein_names = None,None

if "FingerVein" not in list(os.listdir()):
    os.mkdir("FingerVein")

def retrain_completely(KNOWN_finger_vein_DIR = 'FingerVein'):
    global known_finger_vein, known_finger_vein_names

    
    print('Loading known finger_vein...')
    known_finger_vein_temp = []
    known_finger_vein_names_temp = []
    for name in os.listdir(KNOWN_finger_vein_DIR):
        try:
            for filename in os.listdir(f"{KNOWN_finger_vein_DIR}/{name}"):
                try:
                    image_data = fv.load_image_file(f"{KNOWN_finger_vein_DIR}/{name}/{filename}")
                    print("Training for:", filename)
                    code, mask = fv.encode_finger_vein(image_data)
                    known_finger_vein_temp.append([code,mask])
                    known_finger_vein_names_temp.append(name)
                except Exception as e:
                    print('finger_vein not detected', e)
                    # os.remove(f"{KNOWN_finger_vein_DIR}/{name}/{filename}")
        except Exception as e:
            print("Error in retrain Completely", e)

    print(known_finger_vein_names)
    np.save('files1/known_FingerVein', np.array(known_finger_vein_temp))
    np.save('files1/known_FingerVein_names', np.array(known_finger_vein_names_temp))

    known_finger_vein, known_finger_vein_names = None,None

    print("Complete Retraininig Done")

if __name__ == "__main__":
    retrain_completely()