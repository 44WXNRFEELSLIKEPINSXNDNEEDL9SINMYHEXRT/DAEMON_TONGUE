import torch
import re
import pandas as pd
from unidecode import unidecode
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_DIR = "./DAEMON_TONGUE_JUDGE"

# Load tokenizer and model (instantiate once in REPL)
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
model.eval()

# Move model to GPU if available for faster inference
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

def normalize(text: str) -> str:
    text = unidecode(text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.lower().strip()

def predict(phrases: list[str], batch_size: int = 32) -> list[dict]:
    """Accept a list of phrases, run batched inference, return list of result dicts."""
    if not phrases:
        return []
        
    results = []
    
    # Process in batches to balance memory use and speed
    for i in range(0, len(phrases), batch_size):
        batch_phrases = phrases[i : i + batch_size]
        batch_phrases = [normalize(p) for p in batch_phrases]

        inputs = tokenizer(
            batch_phrases, 
            return_tensors="pt", 
            truncation=True,
            padding=True, 
            max_length=128
        ).to(device)
        
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)
            
        # Collect results for this batch
        for phrase, prob in zip(batch_phrases, probs):
            label = int(prob.argmax())
            results.append({
                "phrase": phrase,
                "label": label,            # 1 = daemon, 0 = mortal
                "confidence": round(prob[label].item(), 3),
            })
            
    return results

if __name__ == "__main__":
    while True:
        user_input = input("\nInput: ").strip()
        if len(user_input) > 4000:
            print("Error: Input exceeds 4000 characters. Please enter a shorter phrase.")
            continue
        if not user_input:
            print("Exiting input mode.")
            break
            
        res = predict([user_input])[0]
        
        status = "🔥 DAEMON" if res["label"] == 1 else "✨ MORTAL"
        print(f"Result: {status} | Confidence: {res['confidence'] * 100}%")