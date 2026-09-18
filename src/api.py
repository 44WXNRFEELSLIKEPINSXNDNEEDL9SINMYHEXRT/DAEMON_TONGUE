"""HTTP API around the DAEMON_TONGUE classifier.

Usage:
    uv run uvicorn api:app --app-dir src --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field

from config import LABEL_NAMES
from predict import load_model, predict

MAX_PHRASE_CHARS = 4000
MAX_BATCH = 256


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield


app = FastAPI(title="DAEMON_TONGUE", version="0.1.0", lifespan=lifespan)


class PhraseRequest(BaseModel):
    phrase: str = Field(min_length=1, max_length=MAX_PHRASE_CHARS)


class BatchRequest(BaseModel):
    phrases: list[str] = Field(min_length=1, max_length=MAX_BATCH)


class Judgment(BaseModel):
    phrase: str
    label: int
    name: str
    confidence: float


def to_judgment(result: dict) -> Judgment:
    return Judgment(name=LABEL_NAMES[result["label"]], **result)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/predict", response_model=Judgment)
def judge_one(request: PhraseRequest) -> Judgment:
    return to_judgment(predict([request.phrase])[0])


@app.post("/predict/batch", response_model=list[Judgment])
def judge_batch(request: BatchRequest) -> list[Judgment]:
    return [to_judgment(result) for result in predict(request.phrases, batch_size=64)]
