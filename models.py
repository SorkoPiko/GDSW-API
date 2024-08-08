from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


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


class GJQueryType(Enum):
    SEARCH = 0
    MOST_DOWNLOADED = 1
    MOST_LIKED = 2
    TRENDING = 3
    RECENT = 4
    USER = 5
    FEATURED = 6
    MAGIC = 7
    SENT = 8
    LEVEL_LIST = 10
    AWARDED = 11
    FOLLOWED = 12
    FRIENDS = 13
    GDW = 15
    HALL_OF_FAME = 16
    GDW_FEATURED = 17
    DAILY = 21
    WEEKLY = 22
    LIST = 25


class GJDifficulty(Enum):
    NA = -1
    DEMON = -2
    AUTO = -3
    EASY = 1
    NORMAL = 2
    HARD = 3
    HARDER = 4
    INSANE = 5


class GJDemonFilter(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3
    INSANE = 4
    EXTREME = 5


class GJLength(Enum):
    TINY = 0
    SHORT = 1
    MEDIUM = 2
    LONG = 3
    XL = 4


class getGJLevels21(BaseModel):
    secret: str | None = None
    gameVersion: int | None = None
    binaryVersion: int | None = None
    type: GJQueryType = GJQueryType.MOST_LIKED
    query: str | None = Field(None, alias="str")
    page: int = 0
    total: int | None = None
    gjp2: str | None = None
    accountID: int | None = None
    gdw: bool = False
    gauntlet: int | None = None
    diff: GJDifficulty | None = None
    demonFilter: GJDemonFilter | None = None
    length: list[GJLength] = Field([], alias="len")
    uncompleted: bool = False
    onlyCompleted: bool = False
    completedLevels: list[int] | None = None
    featured: bool = False
    original: bool = False
    twoPlayer: bool = False
    coins: bool = False
    epic: bool = False
    legendary: bool = False
    mythic: bool = False
    noStar: bool = False
    star: bool = False
    song: int | None = None
    customSong: bool = False
    followed: list[int] | None = None
    local: bool = False
    udid: str | None = None
    uuid: str | None = None
