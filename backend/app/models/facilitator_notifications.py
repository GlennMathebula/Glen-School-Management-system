from pydantic import BaseModel


class FacilitatorSessionNotificationRequest(
    BaseModel
):

    force_resend: bool = False