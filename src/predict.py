"""Classify phrases as DAEMON (grimdark) or MORTAL.

Usage:
    uv run src/predict.py          # interactive prompt
"""

import torch
from huggingface_hub.utils import RepositoryNotFoundError
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from config import HF_REPO, LABEL_NAMES, MAX_LEN, MODEL_DIR
from text import normalize

MAX_INPUT_CHARS = 4000

_state: dict = {}


def load_model(revision: str | None = None):
    """Load tokenizer + model once; later calls reuse the cached pair."""
    if _state:
        return _state["tokenizer"], _state["model"], _state["device"]

    local = MODEL_DIR.exists()
    source = str(MODEL_DIR) if local else HF_REPO
    kwargs = {} if local or not revision else {"revision": revision}

    try:
        tokenizer = AutoTokenizer.from_pretrained(source, **kwargs)
        model = AutoModelForSequenceClassification.from_pretrained(source, **kwargs)
    except RepositoryNotFoundError:
        raise SystemExit(
            "Model not found on HuggingFace. Train it first: uv run src/train.py"
        ) from None
    except OSError:
        raise SystemExit(
            "Model files corrupted or incomplete. Retrain: uv run src/train.py"
        ) from None

    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    _state.update(tokenizer=tokenizer, model=model, device=device)
    return tokenizer, model, device


def predict(phrases: list[str], batch_size: int = 32, revision: str | None = None) -> list[dict]:
    """Run batched inference and return one result dict per input phrase."""
    if not phrases:
        return []

    tokenizer, model, device = load_model(revision)
    results = []

    for start in range(0, len(phrases), batch_size):
        batch = phrases[start : start + batch_size]

        inputs = tokenizer(
            [normalize(p) for p in batch],
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=MAX_LEN,
        ).to(device)

        with torch.no_grad():
            probs = torch.softmax(model(**inputs).logits, dim=-1)

        # Keep the caller's original text: staging CSVs are labeled by hand and
        # normalized text is unreadable there.
        for phrase, prob in zip(batch, probs, strict=True):
            label = int(prob.argmax())
            results.append({
                "phrase": phrase,
                "label": label,
                "confidence": round(prob[label].item(), 3),
            })

    return results


def main():
    while True:
        user_input = input("\nInput: ").strip()
        if not user_input:
            print("Exiting input mode.")
            break
        if len(user_input) > MAX_INPUT_CHARS:
            print(f"Error: Input exceeds {MAX_INPUT_CHARS} characters. Enter a shorter phrase.")
            continue

        result = predict([user_input])[0]
        status = "🔥 DAEMON" if result["label"] == 1 else "✨ MORTAL"
        print(f"Result: {status} ({LABEL_NAMES[result['label']]}) "
              f"| Confidence: {result['confidence'] * 100:.1f}%")


if __name__ == "__main__":
    main()
