from fastapi import FastAPI
from services.issuer.routes import router
from common.logging import logger

app = FastAPI(title="ASKP Issuer Service")

app.include_router(router)


@app.on_event("startup")
async def startup():
    logger.info("Issuer Service starting...")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Issuer Service shutting down...")
