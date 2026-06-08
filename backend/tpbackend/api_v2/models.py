from pydantic import BaseModel, Field


class BaseTotals(BaseModel):
    seconds: int = Field(description="Total playtime in seconds")
    activity_count: int = Field(description="Total number of activities")
    last_activity: int | None = Field(description="Timestamp of the last activity")
