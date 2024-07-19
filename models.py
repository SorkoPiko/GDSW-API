from pydantic import BaseModel


class SecretWay(BaseModel):
    id: int
    desc: str
    src: str
    sw: str
    yt: str | None = None


class SecretWayResponse(BaseModel):
    found: bool = False
    data: SecretWay | None = None
