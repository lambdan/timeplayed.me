from pydantic import BaseModel


class Steam_Cover(BaseModel):
    url: str
    store_url: str
