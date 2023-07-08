import json
import os
import zipfile

import cv2
import numpy as np
from flask import Flask, make_response, request, send_file
from PIL import Image
from rembg import remove
import io

app = Flask(__name__)


@app.after_request
def aftert_request(response):
    header = response.headers
    header["Access-Control-Allow-Origin"] = "*"
    header["Access-Control-Allow-Headers"] = "*"
    header["Access-Control-Allow-Methods"] = "*"

    return response


@app.route("/remove_background", methods=["POST"])
def remove_background():
    # Get the uploaded images
    files = request.files.getlist("image")
    original_images = []
    new_images = []

    # Create folders if they don't exist
    if not os.path.exists("user_images/original_images"):
        os.makedirs("user_images/original_images")
    if not os.path.exists("user_images/new_images"):
        os.makedirs("user_images/new_images")

    # Process each image using rembg
    for i, file in enumerate(files):
        img = Image.open(file)
        output = remove(np.array(img.convert("RGB")))

        # Save original image locally
        original_img_path = f"user_images/original_images/original_image_{i}.jpg"
        img.convert("RGB").save(original_img_path)

        # Save output image locally
        new_img_path = f"user_images/new_images/new_image_{i}.png"
        Image.fromarray(output).save(new_img_path)

        original_images.append(original_img_path)
        new_images.append(new_img_path)

    # If only one image was uploaded, return the processed image directly
    if len(new_images) == 1:
        output_img_path = new_images[0]
        return send_file(
            output_img_path,
            mimetype="image/png",
            as_attachment=True,
            attachment_filename="processed_image.png",
        )

    # Otherwise, create a zip file containing all images
    zip_filename = "processed_images.zip"
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for new_image_path in new_images:
            zip_file.write(new_image_path, os.path.basename(new_image_path))

    with open(zip_filename, "rb") as f:
        response_bytes = f.read()

    response = make_response(response_bytes)
    response.headers.set("Content-Type", "application/zip")
    response.headers.set("Content-Disposition", "attachment", filename=zip_filename)
    return response


@app.route("/add_background", methods=["POST"])
def add_background():
    try:
        # Check if the required files are present in the request
        if (
            "foreground_image" not in request.files
            or "background_image" not in request.files
        ):
            return "Foreground and background images are required.", 400

        # Get the foreground and background images from the request
        foreground_image = request.files["foreground_image"]
        background_image = request.files["background_image"]

        # Read the foreground and background images
        foreground = cv2.imdecode(
            np.frombuffer(foreground_image.read(), np.uint8), cv2.IMREAD_COLOR
        )
        background = cv2.imdecode(
            np.frombuffer(background_image.read(), np.uint8), cv2.IMREAD_COLOR
        )

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
        _, encoded_image = cv2.imencode(".jpg", result)

        # Create a file-like object from the encoded image data
        image_stream = io.BytesIO(encoded_image.tobytes())
        image_stream.seek(0)

        # Return the edited image as a file in the response
        return send_file(image_stream, mimetype="image/jpeg")

    except Exception as e:
        return str(e), 500


@app.route("/feedback", methods=["POST"])
def save_feedback():
    feedback = request.get_json()  # Get the feedback from the request body

    with open("feedback.json", "a") as file:
        file.write(json.dumps(feedback))
        file.write("\n")

    return {"message": "Feedback saved successfully."}


if __name__ == "__main__":
    app.run()
