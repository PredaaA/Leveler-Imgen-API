from fastapi import APIRouter, Header
from fastapi.responses import ORJSONResponse
from starlette.responses import StreamingResponse
from pydantic import BaseModel

from app.images import draw_image

router = APIRouter()


class ImageData(BaseModel):
    user: dict
    server: dict
    config: dict


@router.get("/getimage")
async def get_image(
    *, Authorization: str = Header(None), image_type: str = None, payload: ImageData = None
):
    if Authorization is None or Authorization != "nope":
        return ORJSONResponse(
            content={"success": False, "message": "Not authorized."}, status_code=401
        )
    if image_type is None:
        return ORJSONResponse(
            content={"success": False, "message": "image_type arg is missing."}, status_code=400
        )
    if payload is None:
        return ORJSONResponse(
            content={"success": False, "message": "Image data payload is missing."},
            status_code=400,
        )

    data = await draw_image(image_type, payload)
    if data is None:
        return ORJSONResponse(
            content={
                "success": False,
                "message": "bruh idk man something fucked up there is no image.",
            },
            status_code=410,
        )
    return StreamingResponse(content=data, media_type="image/png", status_code=201)
