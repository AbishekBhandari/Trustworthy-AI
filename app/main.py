
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.assistant import answer_question

app = FastAPI(
    title="Trustworthy AI Guardrails",
    description="A demonstration of input and output guardrails.",
    version="0.1.0",
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(request: QuestionRequest):
    return answer_question(request.question)
