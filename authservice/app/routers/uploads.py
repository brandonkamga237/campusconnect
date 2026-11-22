from fastapi import UploadFile

from app.config import settings
from app.errors import ApiError


async def read_image(upload: UploadFile) -> bytes:
    data = await upload.read(settings.face_max_image_bytes + 1)
    if len(data) > settings.face_max_image_bytes:
        raise ApiError(413, "IMAGE_TOO_LARGE", f"The image must not exceed {settings.face_max_image_bytes} bytes")
    if not data:
        raise ApiError(422, "INVALID_IMAGE", "The image is empty")
    return data
