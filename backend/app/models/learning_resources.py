from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
)


# ============================================================
# CREATE TEXT NOTE
# ============================================================

class LearningResourceNoteCreate(
    BaseModel
):

    class_id: str

    module_id: str | None = None

    timetable_session_id: (
        str | None
    ) = None

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = None

    content_text: str = Field(
        min_length=1,
    )


# ============================================================
# CREATE EXTERNAL LINK
# ============================================================

class LearningResourceLinkCreate(
    BaseModel
):

    class_id: str

    module_id: str | None = None

    timetable_session_id: (
        str | None
    ) = None

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = None

    external_url: HttpUrl