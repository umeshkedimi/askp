from fastapi import FastAPI
from services.vault.routes import router
from common.logging import logger

app = FastAPI(title="ASKP Vault Service")

app.include_router(router)


@app.on_event("startup")
async def startup():
    logger.info("Vault Service starting...")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Vault Service shutting down...")
