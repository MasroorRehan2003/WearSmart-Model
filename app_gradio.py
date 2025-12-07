# app_gradio.py
# Single-file Gradio app with per-slot reroll, slot-safe labels, image "DB",
# and optional BLIP captions for fetched images.

import os
import random
from pathlib import Path
from typing import Dict, Tuple, Optional, List

import gradio as gr
import pandas as pd
import joblib
import requests
from PIL import Image

# =======================
# (Optional) BLIP captioning
# =======================
BLIP_AVAILABLE = True
try:
    import torch
    from transformers import BlipProcessor, BlipForConditionalGeneration
except Exception:
    BLIP_AVAILABLE = False
    BlipProcessor = BlipForConditionalGeneration = None

# Small helpers to load BLIP lazily and only once
_blip_loaded = False
_blip_processor = None
_blip_model = None

def _load_blip():
    """Load BLIP model once; CPU/GPU agnostic; safe if unavailable."""
    global _blip_loaded, _blip_processor, _blip_model
    if _blip_loaded or not BLIP_AVAILABLE:
        return
    # Try local fine-tuned folder first, else fallback to base
    local_dir = Path("blip_finetunedggdata")
    try:
        if local_dir.exists():
            _blip_processor = BlipProcessor.from_pretrained(local_dir.as_posix())
            _blip_model = BlipForConditionalGeneration.from_pretrained(local_dir.as_posix())
        else:
            _blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            _blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _blip_model.to(device)
        _blip_loaded = True
    except Exception:
        # If anything fails, disable captions for this run
        _blip_loaded = True
        _blip_processor = None
        _blip_model = None

def generate_caption(image_path: Optional[str]) -> str:
    """Return a short caption for image_path; fallback to '—' if unavailable."""
    if image_path is None:
        return ""
    if not BLIP_AVAILABLE:
        return ""
    if not _blip_loaded:
        _load_blip()
    if _blip_processor is None or _blip_model is None:
        return ""
    try:
        img = Image.open(image_path).convert("RGB")
        inputs = _blip_processor(img, return_tensors="pt").to(_blip_model.device)
        out = _blip_model.generate(**inputs, max_new_tokens=24)
        return _blip_processor.decode(out[0], skip_special_tokens=True)
    except Exception:
        return ""

# ---------------------------------------------------------------------
# scikit-learn pickle compatibility shim (fixes _RemainderColsList)
# ---------------------------------------------------------------------
import importlib
try:
    ct = importlib.import_module("sklearn.compose._column_transformer")
    if not hasattr(ct, "_RemainderColsList"):
        class _RemainderColsList(list):
            """Compat placeholder for models pickled with older scikit-learn."""
            pass
        ct._RemainderColsList = _RemainderColsList
except Exception:
    pass
# ---------------------------------------------------------------------

# -----------------------------
# Config
# -----------------------------
MODEL_PATH = Path("weather_clothing_recommender_women.pkl")
IMAGES_ROOT = Path("clothing_images")  # your "DB" of images
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "4c703f15e3f9220de836884137342d5d")
REQUEST_TIMEOUT = 10

# ---- Allowed labels per slot (must match folder names under clothing_images/) ----
TOP_LABELS = {
    "tops", "shirts", "kurtas"  # extend if you add folders
}
BOTTOM_LABELS = {
    "trousers", "jeans", "leggings", "capris"
}
OUTER_LABELS = {
    "none", "coat", "jacket", "puffer_jacket", "dupatta"
}

def allowed_labels_for(slot: str) -> set:
    if slot == "top":
        return {x.lower() for x in TOP_LABELS}
    if slot == "bottom":
        return {x.lower() for x in BOTTOM_LABELS}
    return {x.lower() for x in OUTER_LABELS}

# -----------------------------
# Weather
# -----------------------------
def fetch_weather(city: str) -> Optional[Dict]:
    if not city:
        return None
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            return None
        d = r.json()
        return {
            "temperature": d["main"]["temp"],
            "feels_like": d["main"]["feels_like"],
            "humidity": d["main"]["humidity"],
            "wind_speed": d["wind"]["speed"],
            "weather_condition": d["weather"][0]["main"].lower(),
        }
    except Exception:
        return None

# -----------------------------
# Model
# -----------------------------
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH.resolve()}")
_model = joblib.load(MODEL_PATH.as_posix())

def predict_outfit(features: Dict) -> Tuple[str, str, str]:
    df = pd.DataFrame([features])
    pred_top, pred_bottom, pred_outer = _model.predict(df)[0]
    return str(pred_top), str(pred_bottom), str(pred_outer)

# -----------------------------
# Image helpers (your "DB")
# -----------------------------
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

def folder_has_images(label: str) -> bool:
    if (label or "").lower() == "none":
        return True
    p = IMAGES_ROOT / (label or "").lower()
    return p.is_dir() and any(f.suffix.lower() in VALID_EXTS for f in p.iterdir())

def pick_image_for_label(label: str, rng: random.Random) -> Optional[str]:
    """Return an image file path for a label; None for 'none' or if not found."""
    if label is None or label.lower() == "none":
        return None
    folder = IMAGES_ROOT / label.lower()
    if not folder.is_dir():
        return None
    files = [p for p in folder.iterdir() if p.suffix.lower() in VALID_EXTS]
    if not files:
        return None
    return rng.choice(files).as_posix()

def sanitize_prediction(label: str, slot: str, rng: random.Random) -> str:
    """Force model output into a valid slot label that has images."""
    allowed = allowed_labels_for(slot)
    lbl = (label or "").lower()
    if lbl in allowed and folder_has_images(lbl):
        return lbl
    candidates = [x for x in allowed if folder_has_images(x)]
    if not candidates:
        return lbl or ""
    return rng.choice(candidates)

def reroll_label(current_label: str, slot: str, rng: random.Random) -> str:
    """Pick a different label within the SAME slot that has images."""
    allowed = allowed_labels_for(slot)
    existing = [lbl for lbl in allowed if folder_has_images(lbl)]
    current = (current_label or "").lower()
    options = [lbl for lbl in existing if lbl != current]
    if not options:
        return current_label
    return rng.choice(options)

# -----------------------------
# Caption cache
# -----------------------------
def get_caption_for_image(path: Optional[str], cache: Dict[str, str]) -> str:
    """
    Return a caption for path, using cache to avoid recomputation.
    When BLIP isn't available, returns "" (we still display label).
    """
    if not path:
        return ""
    if path in cache:
        return cache[path]
    cap = generate_caption(path)
    cache[path] = cap
    return cap

# -----------------------------
# Gradio stateful handlers
# -----------------------------
def do_recommend(city: str, time_of_day: str, season: str, occasion: str, state: Dict):
    weather = fetch_weather(city)
    if weather is None:
        # keep UI as-is on failure
        return (
            "❌ Failed to fetch weather. Check the city name.",
            gr.update(), "Top: (unchanged)",
            gr.update(), "Bottom: (unchanged)",
            gr.update(), "Outerwear: (unchanged)",
            state or {}
        )

    feats = {
        "temperature": weather["temperature"],
        "feels_like": weather["feels_like"],
        "humidity": weather["humidity"],
        "wind_speed": weather["wind_speed"],
        "weather_condition": weather["weather_condition"],
        "time_of_day": time_of_day,
        "season": season,
        "occasion": occasion,
    }

    # model prediction
    pt, pb, po = predict_outfit(feats)

    # seed for consistent picks within this recommendation
    seed = random.randint(0, 10_000_000)
    rng = random.Random(seed)

    # sanitize into correct slots + ensure images exist
    top   = sanitize_prediction(pt, "top", rng)
    bottom= sanitize_prediction(pb, "bottom", rng)
    outer = sanitize_prediction(po, "outer", rng)

    state = state or {}
    state["preds"] = {"top": top, "bottom": bottom, "outer": outer}
    state["seed"] = seed

    # choose images and persist
    images = {
        "top":    pick_image_for_label(top, rng),
        "bottom": pick_image_for_label(bottom, rng),
        "outer":  pick_image_for_label(outer, rng)  # None if outer == 'none'
    }
    state["images"] = images

    # caption cache per session
    captions_cache = {}
    state["captions_cache"] = captions_cache

    # build captions (label + model-generated if available)
    top_cap_model = get_caption_for_image(images["top"], captions_cache)
    top_cap = f"Top: {top}" + (f" — {top_cap_model}" if top_cap_model else "")

    bottom_cap_model = get_caption_for_image(images["bottom"], captions_cache)
    bottom_cap = f"Bottom: {bottom}" + (f" — {bottom_cap_model}" if bottom_cap_model else "")

    if outer == "none":
        outer_cap = "Outerwear: None needed"
    else:
        outer_cap_model = get_caption_for_image(images["outer"], captions_cache)
        outer_cap = f"Outerwear: {outer}" + (f" — {outer_cap_model}" if outer_cap_model else "")

    weather_text = (
        f"🌤️ **{weather['weather_condition'].capitalize()}** | "
        f"🌡️ **{weather['temperature']}°C** (feels {weather['feels_like']}°C) | "
        f"💧 **{weather['humidity']}%** | "
        f"💨 **{weather['wind_speed']} m/s**"
    )

    return (
        weather_text,
        images["top"],    top_cap,
        images["bottom"], bottom_cap,
        images["outer"],  outer_cap,
        state
    )

def do_reroll(slot: str, state: Dict):
    state = state or {}
    preds = state.get("preds") or {}
    images = state.get("images") or {}
    captions_cache = state.get("captions_cache") or {}

    if slot not in {"top", "bottom", "outer"} or not preds.get(slot):
        # nothing to change; keep everything as-is
        return (
            gr.update(),                 # weather
            gr.update(), gr.update(),    # top
            gr.update(), gr.update(),    # bottom
            gr.update(), gr.update(),    # outer
            state
        )

    seed = state.get("seed", random.randint(0, 10_000_000))
    rng = random.Random(seed)

    current = preds[slot]
    new_label = reroll_label(current, slot, rng)
    preds[slot] = new_label
    state["preds"] = preds

    # update only this slot's image
    if slot == "outer" and new_label == "none":
        images["outer"] = None
    else:
        images[slot] = pick_image_for_label(new_label, rng)
    state["images"] = images

    # Update only the changed slot's caption
    if slot == "top":
        cap_model = get_caption_for_image(images["top"], captions_cache)
        cap = f"Top: {new_label}" + (f" — {cap_model}" if cap_model else "")
        return (
            gr.update(),
            images["top"],  cap,
            gr.update(),    gr.update(),
            gr.update(),    gr.update(),
            state
        )

    if slot == "bottom":
        cap_model = get_caption_for_image(images["bottom"], captions_cache)
        cap = f"Bottom: {new_label}" + (f" — {cap_model}" if cap_model else "")
        return (
            gr.update(),
            gr.update(),    gr.update(),
            images["bottom"], cap,
            gr.update(),    gr.update(),
            state
        )

    # slot == "outer"
    if images["outer"] is None:
        cap = "Outerwear: None needed"
        return (
            gr.update(),
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            None, cap,
            state
        )
    else:
        cap_model = get_caption_for_image(images["outer"], captions_cache)
        cap = f"Outerwear: {new_label}" + (f" — {cap_model}" if cap_model else "")
        return (
            gr.update(),
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            images["outer"], cap,
            state
        )

# -----------------------------
# UI
# -----------------------------
with gr.Blocks(title="AI Outfit Recommender") as demo:
    gr.Markdown("## 🧥 AI Clothing Recommender (3-slot reroll + captions, single file)")

    with gr.Row():
        city = gr.Textbox(label="City", placeholder="e.g., Lahore")
        time_of_day = gr.Dropdown(["morning", "afternoon", "evening", "night"], value="morning", label="Time of Day")
        season = gr.Dropdown(["summer", "winter", "spring", "autumn"], value="summer", label="Season")
        occasion = gr.Dropdown(["casual", "formal", "party", "sports"], value="casual", label="Occasion")

    state = gr.State({})

    recommend_btn = gr.Button("💡 Recommend Outfit", variant="primary")
    weather_box = gr.Markdown("")

    with gr.Row():
        top_img = gr.Image(label="Top", type="filepath")
        top_cap = gr.Markdown()
    with gr.Row():
        bottom_img = gr.Image(label="Bottom", type="filepath")
        bottom_cap = gr.Markdown()
    with gr.Row():
        outer_img = gr.Image(label="Outerwear", type="filepath")
        outer_cap = gr.Markdown()

    with gr.Row():
        reroll_top = gr.Button("🔁 Reroll Top")
        reroll_bottom = gr.Button("🔁 Reroll Bottom")
        reroll_outer = gr.Button("🔁 Reroll Outer")

    recommend_btn.click(
        fn=do_recommend,
        inputs=[city, time_of_day, season, occasion, state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state],
    )

    reroll_top.click(
        fn=lambda s: do_reroll("top", s),
        inputs=[state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state],
    )
    reroll_bottom.click(
        fn=lambda s: do_reroll("bottom", s),
        inputs=[state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state],
    )
    reroll_outer.click(
        fn=lambda s: do_reroll("outer", s),
        inputs=[state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state],
    )

if __name__ == "__main__":
    demo.launch()
