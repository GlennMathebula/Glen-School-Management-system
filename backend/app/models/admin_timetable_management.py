
from datetime import date, time
from pydantic import BaseModel, Field

class AdminTimetableSessionCreate(BaseModel):
    class_code: str = Field(min_length=1, max_length=100)
    module_code: str | None = Field(default=None, max_length=150)
    session_title: str | None = Field(default=None, max_length=255)
    session_date: date
    start_time: time
    end_time: time
    delivery_mode: str = Field(default="Physical", max_length=50)
    venue: str | None = Field(default=None, max_length=300)
    meeting_link: str | None = None
    notes: str | None = Field(default=None, max_length=4000)
    status: str = Field(default="Draft", max_length=50)

class AdminTimetableSessionUpdate(BaseModel):
    class_code: str | None = Field(default=None, max_length=100)
    module_code: str | None = Field(default=None, max_length=150)
    session_title: str | None = Field(default=None, max_length=255)
    session_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    delivery_mode: str | None = Field(default=None, max_length=50)
    venue: str | None = Field(default=None, max_length=300)
    meeting_link: str | None = None
    notes: str | None = Field(default=None, max_length=4000)
