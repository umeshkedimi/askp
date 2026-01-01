from fastapi import FastAPI
from services.gateway.routes import router
from common.logging import logger

app = FastAPI(title="ASKP Gateway Service")

app.include_router(router)


@app.on_event("startup")
async def startup():
    logger.info("Gateway Service starting...")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Gateway Service shutting down...")
