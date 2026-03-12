from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str
    request_id: str
    checks: dict[str, str]
