import gradio as gr
from transformers import pipeline

clf = pipeline("text-classification", model="44WXNRFEELSLIKEPINSANDNEEDLESINMYHEART/DAEMON_TONGUE_JUDGE")

def judge(phrase):
    result = clf(phrase)[0]
    label = "🔥 DAEMON" if result["label"] == "LABEL_1" else "✨ MORTAL"
    return f"{label} — {result['score']:.1%}"

gr.Interface(
    fn=judge,
    inputs=gr.Textbox(placeholder="Utter the phrase..."),
    outputs=gr.Textbox(label="Judgment"),
    title="DAEMON_TONGUE_JUDGE",
    description="Does this phrase carry the grimdark aesthetic?"
).launch()