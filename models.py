from pydantic import BaseModel
from typing import Literal
from dataclasses import dataclass
from fastapi import Form


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

@dataclass
class getGJLevels21(BaseModel):
    gameVersion: int = Form(...)
    binaryVersion: int = Form(...)
    udid: str = Form(...)
    uuid: str = Form(...)
    accountID: int = Form(...)
    gjp2: str = Form(...)
    type: int = Form(...)
    str: str = Form(...)
    diff: int = Form(...)
    len: int = Form(...)
    page: int = Form(...)
    total: int = Form(...)
    uncompleted: int = Form(...)
    onlyCompleted: int = Form(...)
    featured: int = Form(...)
    original: int = Form(...)
    twoPlayer: int = Form(...)
    coins: int = Form(...)
    epic: int = Form(...)
    legendary: int = Form(...)
    mythic: int = Form(...)
    song: int = Form(...)
    customSong: int = Form(...)
    noStar: int = Form(...)
    demonFilter: int = Form(...)
    completedLevels: list[int] = Form(...)
    secret: str = Form(...)
