"""Gradio UI for the DAEMON_TONGUE classifier.

Usage:
    uv run src/app.py              # standalone on :7860

Mounted onto the FastAPI app by api.py, so both share one loaded model.
"""

import base64
import html
from pathlib import Path

import gradio as gr

from predict import MAX_INPUT_CHARS, predict

LOGO = Path(__file__).parent / "assets" / "logo.png"

HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?\
family=Bodoni+Moda:ital,opsz,wght@0,6..96,700;1,6..96,700;1,6..96,900&\
family=Spline+Sans:wght@400;500;600&display=swap">
"""

# Palette sampled from the logo: blush #EBCDCC (lettering), mint #79B4B4 (hair).
# Burgundy is the deep register between those two and the black behind them.
VOID = "#0B0609"
SLAB = "#150A0F"
CRYPT = "#1C0D14"
WINE = "#3A1423"
BLOOD = "#8C2340"
SEAR = "#B02E50"
BLUSH = "#EBCDCC"
MINT = "#79B4B4"
MUTE = "#9A7F86"

SANS = '"Spline Sans", ui-sans-serif, system-ui, sans-serif'
DISPLAY = '"Bodoni Moda", Georgia, serif'

# HEAD already pulls both families from Google Fonts (with the italic axis that
# gr.themes.GoogleFont cannot request), so the theme only has to name them.
# Every colour is set on both the light and the dark variant: the page is dark
# either way, so a visitor's system preference cannot half-apply the palette.
THEME = gr.themes.Base(
    primary_hue="rose",
    neutral_hue="stone",
    font=(
        gr.themes.LocalFont("Spline Sans", weights=(400, 500, 600)),
        "ui-sans-serif",
        "system-ui",
        "sans-serif",
    ),
).set(
    body_background_fill=VOID,
    body_background_fill_dark=VOID,
    background_fill_primary=VOID,
    background_fill_primary_dark=VOID,
    background_fill_secondary=CRYPT,
    background_fill_secondary_dark=CRYPT,
    body_text_color=BLUSH,
    body_text_color_dark=BLUSH,
    body_text_color_subdued=MUTE,
    body_text_color_subdued_dark=MUTE,
    border_color_primary=WINE,
    border_color_primary_dark=WINE,
    block_background_fill="transparent",
    block_background_fill_dark="transparent",
    block_border_width="0px",
    block_label_text_color=MUTE,
    block_label_text_color_dark=MUTE,
    block_title_text_color=MUTE,
    block_title_text_color_dark=MUTE,
    input_background_fill=SLAB,
    input_background_fill_dark=SLAB,
    input_background_fill_focus=SLAB,
    input_background_fill_focus_dark=SLAB,
    input_border_color=WINE,
    input_border_color_dark=WINE,
    input_border_color_focus=BLOOD,
    input_border_color_focus_dark=BLOOD,
    input_placeholder_color="#6B4A55",
    input_placeholder_color_dark="#6B4A55",
    input_radius="3px",
    button_large_radius="3px",
    button_small_radius="999px",
    button_secondary_background_fill=BLOOD,
    button_secondary_background_fill_dark=BLOOD,
    button_secondary_background_fill_hover=SEAR,
    button_secondary_background_fill_hover_dark=SEAR,
    button_secondary_border_color=BLOOD,
    button_secondary_border_color_dark=BLOOD,
    button_secondary_text_color=BLUSH,
    button_secondary_text_color_dark=BLUSH,
    button_secondary_text_color_hover=BLUSH,
    button_secondary_text_color_hover_dark=BLUSH,
)

CSS = f"""
:root {{
  --void: {VOID}; --slab: {SLAB}; --crypt: {CRYPT}; --wine: {WINE};
  --blood: {BLOOD}; --sear: {SEAR}; --blush: {BLUSH}; --mint: {MINT};
  --mute: {MUTE};
  --sans: {SANS};
  --display: {DISPLAY};
}}

.gradio-container {{
  max-width: 660px !important;
  margin: 0 auto !important;
  padding: 3.5rem 1.25rem 5rem !important;
}}
footer {{ display: none !important; }}

/* --- masthead --------------------------------------------------------- */
#masthead {{ text-align: center; margin-bottom: 2.4rem; }}
#masthead img {{ display: block; margin: 0 auto; width: min(100%, 420px); height: auto; }}
#masthead .wordmark {{
  color: var(--blush);
  font-family: var(--display);
  font-size: 3rem;
  font-style: italic;
  font-weight: 900;
  margin: 0;
}}
#masthead p {{
  margin: 0.6rem auto 0;
  max-width: 44ch;
  font-size: 0.95rem;
  line-height: 1.65;
  color: var(--mute);
}}

/* --- the phrase you submit -------------------------------------------- */
#phrase, #phrase .container {{
  background: none !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}}
#phrase textarea {{
  border: 1px solid var(--wine);
  border-radius: 3px;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.5);
  color: var(--blush);
  font-family: var(--display);
  font-size: 1.3rem;
  line-height: 1.55;
  padding: 1.05rem 1.15rem;
  resize: none;
}}
#phrase textarea::placeholder {{ font-style: italic; }}
#phrase .container > span {{ display: none !important; }}

#judge {{
  margin-top: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  padding: 0.85rem 1rem;
}}

/* --- the verdict ------------------------------------------------------- */
#verdict {{ margin-top: 1.6rem; }}
.verdict {{
  background: var(--crypt);
  border: 1px solid var(--wine);
  border-radius: 3px;
  padding: 1.9rem 1.5rem 1.8rem;
  text-align: center;
}}
.verdict--idle {{
  background: none;
  border-style: dashed;
  color: var(--mute);
  font-family: var(--display);
  font-size: 1.15rem;
  font-style: italic;
  padding: 2.8rem 1.5rem;
}}
.verdict--error {{
  border-color: var(--blood);
  color: var(--blush);
  font-size: 0.95rem;
  line-height: 1.6;
}}
.verdict p {{ margin: 0; }}

/* The scale: a beam that fills from its pivot toward the winning pole. */
.scale {{ display: flex; align-items: center; gap: 0.9rem; }}
.scale__pole {{
  color: var(--mute);
  flex: 0 0 auto;
  font-family: var(--sans);
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  transition: color 0.3s ease;
}}
.scale__pole--mortal.is-won {{ color: var(--mint); }}
.scale__pole--daemon.is-won {{ color: var(--sear); }}
.scale__beam {{
  background: #2E1520;
  border-radius: 1px;
  flex: 1 1 auto;
  height: 3px;
  position: relative;
}}
.scale__fill {{
  border-radius: 1px;
  height: 100%;
  position: absolute;
  top: 0;
  transition: left 0.45s cubic-bezier(0.22, 1, 0.36, 1),
              width 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}}
.verdict--daemon .scale__fill {{ background: var(--sear); }}
.verdict--mortal .scale__fill {{ background: var(--mint); }}
.scale__pivot {{
  background: var(--mute);
  height: 11px;
  left: 50%;
  opacity: 0.5;
  position: absolute;
  top: -4px;
  transform: translateX(-50%);
  width: 1px;
}}

.verdict__word {{
  font-family: var(--display);
  font-size: clamp(2.9rem, 12vw, 4.4rem);
  font-style: italic;
  font-weight: 900;
  line-height: 1.05;
  margin: 1.2rem 0 0 !important;
}}
.verdict--daemon .verdict__word {{ color: var(--blush); }}
.verdict--mortal .verdict__word {{ color: var(--mint); }}
.verdict__meta {{
  color: var(--mute);
  font-size: 0.85rem;
  margin-top: 0.4rem !important;
}}
/* --- starting points --------------------------------------------------- */
#seeds {{ margin-top: 2.4rem; }}
#seeds .label svg {{ display: none !important; }}
#seeds .label {{
  color: var(--mute) !important;
  font-size: 0.82rem !important;
  margin-bottom: 0.7rem;
}}
#seeds .gallery {{
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 0.5rem !important;
}}
#seeds .gallery-item {{
  background: var(--slab) !important;
  border: 1px solid var(--wine) !important;
  border-radius: 999px !important;
  color: var(--mute) !important;
  padding: 0.42rem 0.95rem !important;
  transition: border-color 0.15s ease, color 0.15s ease;
}}
#seeds .gallery-item div {{
  font-family: var(--display) !important;
  font-size: 0.95rem !important;
  font-style: italic;
  width: auto !important;
}}
#seeds .gallery-item:hover {{
  border-color: var(--blood) !important;
  color: var(--blush) !important;
}}

@media (max-width: 480px) {{
  .verdict {{ padding: 1.6rem 1.1rem 1.5rem; }}
  .scale {{ gap: 0.55rem; }}
  .scale__pole {{ font-size: 0.7rem; letter-spacing: 0.03em; }}
}}

@media (prefers-reduced-motion: reduce) {{
  .scale__fill, .scale__pole, #judge, #seeds .gallery-item {{
    transition: none !important;
  }}
}}
"""

IDLE = '<div class="verdict verdict--idle">Speak, and be judged.</div>'


def _error(message: str) -> str:
    return f'<div class="verdict verdict--error">{html.escape(message)}</div>'


def _logo_tag() -> str:
    if not LOGO.exists():
        return '<p class="wordmark">DaemonTongue</p>'
    data = base64.b64encode(LOGO.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{data}" alt="DaemonTongue">'


def judge(phrase: str) -> str:
    """Classify one phrase and render the verdict panel."""
    phrase = (phrase or "").strip()
    if not phrase:
        return IDLE
    if len(phrase) > MAX_INPUT_CHARS:
        return _error(
            f"That phrase runs to {len(phrase):,} characters. "
            f"Trim it under {MAX_INPUT_CHARS:,} and try again."
        )

    result = predict([phrase])[0]
    is_daemon = result["label"] == 1
    confidence = result["confidence"]

    # The beam fills from its pivot toward the winning pole, so both ends are
    # positioned off the DAEMON probability rather than the raw confidence.
    p_daemon = confidence if is_daemon else 1 - confidence
    left, right = sorted((0.5, p_daemon))

    side = "daemon" if is_daemon else "mortal"
    won = ("", " is-won") if is_daemon else (" is-won", "")

    return f"""
<div class="verdict verdict--{side}">
  <div class="scale">
    <span class="scale__pole scale__pole--mortal{won[0]}">Mortal</span>
    <div class="scale__beam">
      <div class="scale__fill" style="left:{left:.2%};width:{right - left:.2%}"></div>
      <div class="scale__pivot"></div>
    </div>
    <span class="scale__pole scale__pole--daemon{won[1]}">Daemon</span>
  </div>
  <p class="verdict__word">{"Daemon" if is_daemon else "Mortal"}</p>
  <p class="verdict__meta">{confidence:.1%} certain</p>
</div>
"""


with gr.Blocks(title="DaemonTongue", fill_width=False) as demo:
    gr.HTML(
        f'<div id="masthead">{_logo_tag()}'
        "<p>A phrase is either grimdark or it isn't. Submit one and find out "
        "which side of the line it falls on.</p></div>",
        elem_id="masthead-wrap",
    )

    phrase = gr.Textbox(
        elem_id="phrase",
        lines=2,
        max_lines=6,
        placeholder="Utter a phrase…",
        show_label=False,
        submit_btn=False,
    )
    submit = gr.Button("Pass judgment", elem_id="judge")
    verdict = gr.HTML(IDLE, elem_id="verdict")

    gr.Examples(
        examples=[
            ["the dark is patient"],
            ["lunch is at one"],
            ["salt in every wound"],
            ["have a lovely weekend"],
        ],
        inputs=phrase,
        label="Or start from one of these",
        elem_id="seeds",
    )

    gr.on(
        triggers=[submit.click, phrase.submit],
        fn=judge,
        inputs=phrase,
        outputs=verdict,
        api_name="judge",
    )


if __name__ == "__main__":
    demo.launch(theme=THEME, css=CSS, head=HEAD)
