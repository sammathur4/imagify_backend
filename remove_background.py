import os
import zipfile
import numpy as np
from flask import Flask, request, send_file, make_response
from rembg import remove
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = 'user_images'
ORIGINAL_FOLDER = os.path.join(UPLOAD_FOLDER, 'original_images')
NEW_FOLDER = os.path.join(UPLOAD_FOLDER, 'new_images')

# Create folders if they don't exist
os.makedirs(ORIGINAL_FOLDER, exist_ok=True)
os.makedirs(NEW_FOLDER, exist_ok=True)
@app.route('/remove_background', methods=['POST'])
def remove_background():
    try:
        # Get the uploaded images
        files = request.files.getlist('image')
        original_images = []
        new_images = []

        # Create folders if they don't exist
        os.makedirs('user_images/original_images', exist_ok=True)
        os.makedirs('user_images/new_images', exist_ok=True)

        # Process each image using rembg
        for i, file in enumerate(files):
            img = Image.open(file)
            output = remove(np.array(img.convert('RGB')))

            # Save original image locally
            original_img_path = f'user_images/original_images/original_image_{i}.jpg'
            img.convert('RGB').save(original_img_path)
            original_images.append(original_img_path)

            # Save output image locally
            new_img_path = f'user_images/new_images/new_image_{i}.png'
            Image.fromarray(output).save(new_img_path)
            new_images.append(new_img_path)

        if len(new_images) == 1:
            # If only one image was uploaded, return the processed image directly
            output_img_path = new_images[0]
            with open(output_img_path, 'rb') as f:
                response_bytes = f.read()

            response = make_response(response_bytes)
            response.headers.set('Content-Type', 'image/png')
            response.headers.set('Content-Disposition', 'attachment', filename='processed_image.png')
            return response

        zip_filename = 'processed_images.zip'
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for new_image_path in new_images:
                zip_file.write(new_image_path, os.path.basename(new_image_path))

        with open(zip_filename, 'rb') as f:
            response_bytes = f.read()

        response = make_response(response_bytes)
        response.headers.set('Content-Type', 'application/zip')
        response.headers.set('Content-Disposition', 'attachment', filename=zip_filename)
        return response
    except Exception as e:
        return str(e), 500


if __name__ == '__main__':
    app.run()
