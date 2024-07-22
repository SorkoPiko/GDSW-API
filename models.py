from pydantic import BaseModel
from typing import Literal


class Route(BaseModel):
    start: int | None
    end: int | None
    desc: str
    type: Literal["normal", "minigame", "other"]


class SecretWay(BaseModel):
    src: str
    routes: list[Route]
    yt: str | None = None


class SecretWayResponse(BaseModel):
    found: bool = False
    data: SecretWay | None = None
