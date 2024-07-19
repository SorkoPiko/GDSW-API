from pydantic import BaseModel


class SecretWayResponse(BaseModel):
    id: int
    desc: str | None
    src: str | None
    sw: str | None
    yt: str | None = None
