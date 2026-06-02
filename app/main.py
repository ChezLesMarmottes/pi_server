import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.routes.devices import devices_router
from app.routes.health import health_router
from app.routes.measurements import measurements_router
from app.routes.rules import rules_router

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", level=logging.INFO)

logger: logging.Logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Server started")
    yield
    logger.info("Server stopped")

app: FastAPI = FastAPI(lifespan=lifespan)

app.include_router(devices_router, prefix="/devices")
app.include_router(health_router, prefix="/health")
app.include_router(measurements_router, prefix="/measurements")
app.include_router(rules_router, prefix="/rules")