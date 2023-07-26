import os
import zipfile

import numpy as np
from fastapi import Response, UploadFile
from fastapi.routing import APIRouter
from PIL import Image
from rembg import new_session, remove

router = APIRouter()


@router.post("", include_in_schema=False)
@router.post("/")
def remove_background(image: list[UploadFile]):
    original_images = []
    new_images = []

    # Create folders if they don't exist
    os.makedirs("user_images/original_images", exist_ok=True)
    os.makedirs("user_images/new_images", exist_ok=True)

    # Process each image using rembg
    for i, file in enumerate(image):
        img = Image.open(file.file)
        session = new_session("isnet-general-use")
        output = remove(np.array(img.convert("RGB")), session=session)

        # Save original image locally
        original_img_path = f"user_images/original_images/original_image_{i}.jpg"
        img.convert("RGB").save(original_img_path)
        original_images.append(original_img_path)

        # Save output image locally
        new_img_path = f"user_images/new_images/new_image_{i}.png"
        Image.fromarray(output).save(new_img_path)
        new_images.append(new_img_path)

    if len(new_images) == 1:
        # If only one image was uploaded, return the processed image directly
        output_img_path = new_images[0]
        with open(output_img_path, "rb") as f:
            response_bytes = f.read()

        headers = {
            "Content-Type": "image/png",
            "Content-Disposition": f'attachment; filename="processed_image.png"',
        }
        return Response(content=response_bytes, headers=headers)

    zip_filename = "processed_images.zip"
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for new_image_path in new_images:
            zip_file.write(new_image_path, os.path.basename(new_image_path))

    with open(zip_filename, "rb") as f:
        response_bytes = f.read()

    headers = {
        "Content-Type": "application/zip",
        "Content-Disposition": f'attachment; filename="{zip_filename}"',
    }

    return Response(content=response_bytes, headers=headers)


@router.post("/lowres")
def post_remove_background_lowres(image: list[UploadFile]):
    original_images = []
    new_images = []

    # Create folders if they don't exist
    os.makedirs("user_images/original_images", exist_ok=True)
    os.makedirs("user_images/new_images", exist_ok=True)

    # Process each image using rembg
    for i, file in enumerate(image):
        img = Image.open(file.file)
        session = new_session("isnet-general-use")

        max_dimm = max(img.size)
        if max_dimm > 512:
            scale = 512 / max_dimm
            img = img.resize((round(img.size[0] * scale), round(img.size[1] * scale)))

        output = remove(np.array(img.convert("RGB")), session=session)

        # Save original image locally
        original_img_path = f"user_images/original_images/original_image_{i}.jpg"
        img.convert("RGB").save(original_img_path)
        original_images.append(original_img_path)

        # Save output image locally
        new_img_path = f"user_images/new_images/new_image_{i}.png"
        Image.fromarray(output).save(new_img_path)
        new_images.append(new_img_path)

    if len(new_images) == 1:
        # If only one image was uploaded, return the processed image directly
        output_img_path = new_images[0]
        with open(output_img_path, "rb") as f:
            response_bytes = f.read()

        headers = {
            "Content-Type": "image/png",
            "Content-Disposition": f'attachment; filename="processed_image.png"',
        }
        return Response(content=response_bytes, headers=headers)

    zip_filename = "processed_images.zip"
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for new_image_path in new_images:
            zip_file.write(new_image_path, os.path.basename(new_image_path))

    with open(zip_filename, "rb") as f:
        response_bytes = f.read()

    headers = {
        "Content-Type": "application/zip",
        "Content-Disposition": f'attachment; filename="{zip_filename}"',
    }

    return Response(content=response_bytes, headers=headers)
