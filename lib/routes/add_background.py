import io

import cv2
import numpy as np
from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter

router = APIRouter()


@router.post("", include_in_schema=False)
@router.post("/")
async def add_background(foreground_image: UploadFile, background_image: UploadFile):
    # Read the foreground and background images
    foreground = cv2.imdecode(
        np.frombuffer(await foreground_image.read(), np.uint8), cv2.IMREAD_COLOR
    )
    background = cv2.imdecode(
        np.frombuffer(await background_image.read(), np.uint8), cv2.IMREAD_COLOR
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
    # return send_file(image_stream, mimetype="image/jpeg")
    return StreamingResponse(content=image_stream, media_type="image/jpeg")
