import numpy as np
import pandas as pd
from datasets import Dataset
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

MODEL_NAME  = "roberta-base"
DATA_PATH   = "dataset.csv"
OUTPUT_DIR  = "./DAEMON_TONGUE_JUDGE"
NUM_LABELS  = 2
EPOCHS      = 4
BATCH_SIZE  = 16
MAX_LEN     = 128
LR          = 2e-5


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    if isinstance(logits, tuple):
        logits = logits[0]
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1": f1_score(labels, preds, average="binary"),
    }

def main():
    df = pd.read_csv(DATA_PATH)
    assert {"phrase", "label"}.issubset(df.columns)

    df = df.dropna(subset=["phrase", "label"])
    df["phrase"] = df["phrase"].astype(str)
    df["label"]  = df["label"].astype(int)

    train_df, val_df = train_test_split(
        df, test_size=0.15, stratify=df["label"], random_state=42
    )

    train_df = train_df.reset_index(drop=True)
    val_df   = val_df.reset_index(drop=True)

    print(f"Train: {len(train_df)}  |  Val: {len(val_df)}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model     = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=NUM_LABELS
    )

    train_hf = Dataset.from_pandas(
        train_df[["phrase", "label"]].rename(columns={"label": "labels"})
    )
    val_hf = Dataset.from_pandas(
        val_df[["phrase", "label"]].rename(columns={"label": "labels"})
    )

    def tokenize_function(examples):
        return tokenizer(examples["phrase"], truncation=True, max_length=MAX_LEN)

    train_dataset = train_hf.map(tokenize_function, batched=True).remove_columns(["phrase"])
    val_dataset   = val_hf.map(tokenize_function, batched=True).remove_columns(["phrase"])

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    args = TrainingArguments(
        output_dir                  = OUTPUT_DIR,
        num_train_epochs            = EPOCHS,
        per_device_train_batch_size = BATCH_SIZE,
        per_device_eval_batch_size  = BATCH_SIZE,
        learning_rate               = LR,
        weight_decay                = 0.01,
        warmup_ratio                = 0.1,
        eval_strategy               = "epoch",
        save_strategy               = "epoch",
        load_best_model_at_end      = True,
        metric_for_best_model       = "f1",
        logging_steps               = 20,
        report_to                   = "none",
        fp16                        = True,
        seed                        = 1000 - 7,
    )

    trainer = Trainer(
        model           = model,
        args            = args,
        train_dataset   = train_dataset,
        eval_dataset    = val_dataset,
        data_collator   = data_collator,
        compute_metrics = compute_metrics,
    )

    trainer.train()
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\nModel saved to {OUTPUT_DIR}")

    preds_output = trainer.predict(val_dataset)
    logits = (
        preds_output.predictions[0]
        if isinstance(preds_output.predictions, tuple)
        else preds_output.predictions
    )
    preds = np.argmax(logits, axis=-1)

    print("\n── Validation Report ──")
    print(classification_report(
        val_df["label"], preds, target_names=["mortal", "daemon"]
    ))

if __name__ == "__main__":
    main()