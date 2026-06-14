from pydantic import BaseModel


class Data(BaseModel):
    label: str
    data: list[int]


class PlaytimeChart(BaseModel):
    labels: list[str]
    datasets: list[Data]
