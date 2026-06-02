from fastapi import APIRouter

health_router = APIRouter()

@health_router.get("")
def get_health() -> dict[str, str]:
    return {"status": "ok"}