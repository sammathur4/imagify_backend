import json
import os
import zipfile
import numpy as np
from flask import Flask, request, make_response, send_file, jsonify
from rembg import remove
from PIL import Image
import threading
import cv2
import io

app = Flask(__name__)


@app.route('/remove_background', methods=['POST'])
def remove_background():
    # Get the uploaded images
    files = request.files.getlist('image')
    vals = [files]
    print(len(vals))
    original_images = []
    new_images = []

    # Create folders if they don't exist
    if not os.path.exists('user_images/original_images'):
        os.makedirs('user_images/original_images')
    if not os.path.exists('user_images/new_images'):
        os.makedirs('user_images/new_images')

    # Process each image using rembg
    for i, file in enumerate(files):
        img = Image.open(file)
        output = remove(np.array(img.convert('RGB')))

        # Save original image locally
        original_img_path = f'user_images/original_images/original_image_{i}.jpg'
        img.convert('RGB').save(original_img_path)

        # Save output image locally
        new_img_path = f'user_images/new_images/new_image_{i}.png'
        Image.fromarray(output).save(new_img_path)

        original_images.append(original_img_path)
        new_images.append(new_img_path)

    # If only one image was uploaded, return the processed image directly
    if len(new_images) == 1:
        output_img_path = new_images[0]
        with open(output_img_path, 'rb') as f:
            output_img_bytes = f.read()

        # Delete uploaded images after 60 minutes
        threading.Timer(3600, lambda: delete_files(original_images + new_images)).start()

        response = make_response(output_img_bytes)
        response.headers.set('Content-Type', 'image/png')
        return response

    # Otherwise, create a zip file containing all images
    zip_filename = 'processed_images.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for original_image_path, new_image_path in zip(original_images, new_images):
            zip_file.write(original_image_path, os.path.basename(original_image_path))
            zip_file.write(new_image_path, os.path.basename(new_image_path))

    # Delete uploaded images after 60 minutes
    threading.Timer(3600, lambda: delete_files(original_images + new_images + [zip_filename])).start()

    # Create response with zip file
    with open(zip_filename, 'rb') as f:
        response_bytes = f.read()

    response = make_response(response_bytes)
    response.headers.set('Content-Type', 'application/zip')
    response.headers.set('Content-Disposition', 'attachment', filename=zip_filename)
    return response


def delete_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.route('/add_background', methods=['POST'])
def add_background():
    try:
        # Check if the required files are present in the request
        if 'foreground_image' not in request.files or 'background_image' not in request.files:
            return "Foreground and background images are required.", 400

        # Get the foreground and background images from the request
        foreground_image = request.files['foreground_image']
        background_image = request.files['background_image']

        # Read the foreground and background images
        foreground = cv2.imdecode(np.frombuffer(foreground_image.read(), np.uint8), cv2.IMREAD_COLOR)
        background = cv2.imdecode(np.frombuffer(background_image.read(), np.uint8), cv2.IMREAD_COLOR)

        # Resize the foreground image to match the background image dimensions
        foreground = cv2.resize(foreground, (background.shape[1], background.shape[0]))

        # Create a binary mask from the foreground image (assumes white pixels as foreground)
        foreground_mask = cv2.cvtColor(foreground, cv2.COLOR_BGR2GRAY)
        _, foreground_mask = cv2.threshold(foreground_mask, 1, 255, cv2.THRESH_BINARY)

        # Invert the mask (background pixels will be white)
        background_mask = cv2.bitwise_not(foreground_mask)

        # Apply the masks to the foreground and background images
        foreground = cv2.bitwise_and(foreground, foreground, mask=foreground_mask)
        background = cv2.bitwise_and(background, background, mask=background_mask)

        # Combine the foreground and background images
        result = cv2.add(foreground, background)

        # Encode the resulting image to JPEG format
        _, encoded_image = cv2.imencode('.jpg', result)

        # Create a file-like object from the encoded image data
        image_stream = io.BytesIO(encoded_image.tobytes())
        image_stream.seek(0)

        # Return the edited image as a file in the response
        return send_file(image_stream, mimetype='image/jpeg')

    except Exception as e:
        return str(e), 500


@app.route('/feedback', methods=['POST'])
def save_feedback():
    feedback = request.get_json()  # Get the feedback from the request body

    with open('feedback.json', 'a') as file:
        file.write(json.dumps(feedback))
        file.write("\n")

    return {'message': 'Feedback saved successfully.'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
