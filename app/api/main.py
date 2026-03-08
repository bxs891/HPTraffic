import logging

from fastapi import FastAPI

from app.config.logging import configure_logging
from app.config.settings import settings
from app.schemas.health import HealthzResponse

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)


@app.get("/healthz", response_model=HealthzResponse)
def healthz() -> HealthzResponse:
    logger.info("healthz checked")
    return HealthzResponse()
