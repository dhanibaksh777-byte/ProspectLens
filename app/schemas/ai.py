from pydantic import BaseModel


class MatchExplanationResponse(BaseModel):
    explanation: str


class OutreachDraftRequest(BaseModel):
    channel: str = "email"  # "email" or "whatsapp"


class OutreachDraftResponse(BaseModel):
    draft: str
    channel: str
