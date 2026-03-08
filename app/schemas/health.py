from pydantic import BaseModel


class HealthzResponse(BaseModel):
    status: str = "ok"
