from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.redis_client import get_redis_health


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/redis")
def redis_health(response: Response):
    result = get_redis_health()

    if not result.get("healthy"):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return result