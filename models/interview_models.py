from pydantic import BaseModel
from typing import List, Literal

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class InterviewStartRequest(BaseModel):
    interviewType: str

class InterviewStartResponse(BaseModel):
    response: str

class InterviewNextRequest(BaseModel):
    interviewType: str
    conversation: List[Message]

class InterviewNextResponse(BaseModel):
    response: str

class InterviewEvaluationRequest(BaseModel):
    conversation: List[Message]

class InterviewEvaluationResponse(BaseModel):
    overall_evaluation: str
    strengths: List[str]
    weaknesses: List[str]
    missing_keywords: List[str]
    score: float