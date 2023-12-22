import os
from google.cloud import storage
from flask import Flask, request, jsonify
from io import BytesIO

import pickle
import tensorflow as tf
import numpy as np
from numpy.linalg import norm
import os
from tqdm import tqdm
import pickle
import shutil
import PIL
import cv2

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.preprocessing import image
from tensorflow.keras.layers import GlobalMaxPooling2D
from tensorflow.keras.applications.resnet50 import ResNet50,preprocess_input
from sklearn.neighbors import NearestNeighbors

app = Flask(__name__)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'Credentials.json'
storage_client = storage.Client()

#Feature
feature_batik = storage_client.get_bucket('feature_product.pkl')
feature_list = np.array(pickle.load(open(tb_products,'rb')))

product_name = storage_client.get_bucket('product_name.pkl')
filenames = pickle.load(open(product_name,'rb'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            tb_products = storage_client.get_bucket('tb_products')
            product_image = request.json['product_image']
            product_blob = tb_products.blob('images/' + product_image)
            img_path = BytesIO(product_blob.download_as_bytes())
        except Exception:
            respond = jsonify({'message': 'Error loading image file'})
            respond.status_code = 400
            return respond

        def preprocessingImg(image_path):
            img = image.load_img(image_path, target_size=(224, 224))
            img_array = image.img_to_array(img)
            expanded_img_array = np.expand_dims(img_array, axis=0)
            preprocessed_img = preprocess_input(expanded_img_array)

            return preprocessed_img

        def Model():
            # Load ResNet50 model without top classification layers
            base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
            # Freeze layers in base model
            for layer in base_model.layers:
                layer.trainable = False

            model = tf.keras.Sequential([
                base_model,
                GlobalMaxPooling2D()
            ])
            return model

        model = Model()

        def NormalizedImage(preprocessed_img, model):
            result = model.predict(preprocessed_img).flatten()
            normalized_result = result / norm(result)

            return normalized_result

        def Nearest(feature_list, NormalizedImage):
            neighbors = NearestNeighbors(n_neighbors=6, algorithm='brute', metric='euclidean')
            neighbors.fit(feature_list) #feature_list from feature_batik.pkl
            distances, indices = neighbors.kneighbors([NormalizedImage])

            return indices

        process_image = preprocessingImg(image_path)
        NormalizedImage = NormalizedImage(process_image, model)
        indices_image = Nearest(feature_list, NormalizedImage)

        tb_product = []
        count = 0  # Initialize a counter
        for file in indices_image[0]:
            if count >= 5:  # Limit the collection to 5 images
                break

            img_path = filenames[file] #image/
            if img_path is not None:
                height, width = img_path.shape
                # Add image information to the list
                tb_product.append({
                    'product_image': img_path,
                    'height' : height,
                    'width' : width,
                })

                count += 1  # Increment counter after processing an image
            else:
                print(f"Could not read image: {img_path}")

        respond = jsonify(tb_product)
        respond.status_code = 200
        return respond

    return 'OK'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
