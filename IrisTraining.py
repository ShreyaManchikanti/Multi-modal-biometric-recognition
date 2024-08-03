# Dataset link : https://www.kaggle.com/datasets/naureenmohammad/mmu-iris-dataset

import Iris__gabor_module as ir
import numpy as np
import os

known_iris, known_iris_names = None,None

if "iris" not in list(os.listdir()):
    os.mkdir("iris")

def retrain_completely(KNOWN_IRIS_DIR='iris'):
    global known_iris, known_iris_names

    print('Loading known iris...')
    known_iris_temp = []
    known_iris_names_temp = []
    for name in os.listdir(KNOWN_IRIS_DIR):
        try:
            for filename in os.listdir(f"{KNOWN_IRIS_DIR}/{name}"):
                try:
                    image_data = ir.load_image_file(f"{KNOWN_IRIS_DIR}/{name}/{filename}")
                    print("Training for:", filename)
                    code, mask = ir.encode_iris(image_data)
                    known_iris_temp.append([code, mask])
                    known_iris_names_temp.append(name)
                except Exception as e:
                    print('Iris not detected', e)
        except Exception as e:
            print("Error in retrain completely", e)

    np.save('files1/known_iris', np.array(known_iris_temp))
    np.save('files1/known_iris_names', np.array(known_iris_names_temp))

    known_iris, known_iris_names = np.array(known_iris_temp), np.array(known_iris_names_temp)

    print("Complete Retraining Done")

if __name__ == "__main__":
    retrain_completely()