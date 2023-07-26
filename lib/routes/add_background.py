import io
from typing import Annotated
from PIL import Image

from fastapi import Form, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter

router = APIRouter()


@router.post("", include_in_schema=False)
@router.post("/")
async def add_background(
    foreground_image: UploadFile,
    background_image: UploadFile,
    scale_fg: Annotated[float, Form()],
    offset_x: Annotated[int, Form()],
    offset_y: Annotated[int, Form()],
):
    foreground = Image.open(foreground_image.file)
    background = Image.open(background_image.file)

    scaled_w = round(foreground.size[0] * scale_fg)
    scaled_h = round(foreground.size[1] * scale_fg)
    foreground = foreground.resize((scaled_w, scaled_h))

    background.paste(foreground, (offset_x, offset_y), foreground)

    image_stream = io.BytesIO()
    background.save(image_stream, "JPEG")
    image_stream.seek(0)

    return StreamingResponse(content=image_stream, media_type="image/jpeg")


@router.post("/lowres")
async def add_background_lowres(
    foreground_image: UploadFile,
    background_image: UploadFile,
    scale_fg: Annotated[float, Form()],
    offset_x: Annotated[int, Form()],
    offset_y: Annotated[int, Form()],
):
    foreground = Image.open(foreground_image.file)
    background = Image.open(background_image.file)

    scaled_w = round(foreground.size[0] * scale_fg)
    scaled_h = round(foreground.size[1] * scale_fg)
    foreground = foreground.resize((scaled_w, scaled_h))

    background.paste(foreground, (offset_x, offset_y), foreground)

    max_dimm = max(background.size)
    if max_dimm > 512:
        scale = 512 / max_dimm
        background = background.resize(
            (round(background.size[0] * scale), round(background.size[1] * scale))
        )

    image_stream = io.BytesIO()
    background.save(image_stream, "JPEG")
    image_stream.seek(0)

    return StreamingResponse(content=image_stream, media_type="image/jpeg")
