from fastapi import FastAPI
import asyncio

from app.routers.images import router
from app.images.image import session
from app.images.db.mongodb import mongodb


app = FastAPI(
    title="Leveler Image generation API",
    version="idk",
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)
app.include_router(router)


@app.on_event("startup")
async def startup():
    await mongodb.initialize()


@app.on_event("shutdown")
async def shutdown():
    await mongodb.disconnect()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(session.close())
