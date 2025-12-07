# app_gradio_men.py
# Men module — per-slot image shuffle (keeps label), slot-safe labels, MEN-conditioned captions

import os
import random
from pathlib import Path
from typing import Dict, Tuple, Optional

import gradio as gr
import pandas as pd
import joblib
import requests
from PIL import Image

# ======================================
# Captioning config (toggle here)
# ======================================
ENABLE_CAPTIONS = True
CAPTION_AUDIENCE = "men"   # used in prompts and normalization (men | women | unisex)

# =======================
# (Optional) BLIP captions
# =======================
BLIP_AVAILABLE = ENABLE_CAPTIONS
try:
    if ENABLE_CAPTIONS:
        import torch
        from transformers import BlipProcessor, BlipForConditionalGeneration
    else:
        BLIP_AVAILABLE = False
except Exception:
    BLIP_AVAILABLE = False
    BlipProcessor = BlipForConditionalGeneration = None

_blip_loaded = False
_blip_processor = None
_blip_model = None

def _pick_blip_dir() -> Optional[Path]:
    # Prefer a MEN fine-tune if you have it; never auto-load women's ft.
    env_dir = os.getenv("BLIP_LOCAL_DIR")
    if env_dir and Path(env_dir).exists():
        return Path(env_dir)
    men_dir = Path("blip_finetuned_men")
    if men_dir.exists():
        return men_dir
    return None

def _load_blip():
    global _blip_loaded, _blip_processor, _blip_model
    if _blip_loaded or not BLIP_AVAILABLE:
        return
    local_dir = _pick_blip_dir()
    try:
        if local_dir is not None:
            _blip_processor = BlipProcessor.from_pretrained(local_dir.as_posix())
            _blip_model = BlipForConditionalGeneration.from_pretrained(local_dir.as_posix())
        else:
            _blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            _blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        device = "cuda" if ("torch" in globals() and torch.cuda.is_available()) else "cpu"
        _blip_model.to(device)
        _blip_loaded = True
    except Exception:
        _blip_loaded = True
        _blip_processor = None
        _blip_model = None

def _normalize_caption_gender(cap: str, audience: str) -> str:
    if not cap:
        return cap
    repls = {
        "for women": f"for {audience}",
        "for woman": f"for {audience}",
        "women's": f"{audience}'s",
        "woman's": f"{audience}'s",
        "female": audience,
        "ladies": audience,
    }
    out = cap
    for k, v in repls.items():
        out = out.replace(k, v)
    return out

def generate_caption(image_path: Optional[str], slot_hint: Optional[str] = None) -> str:
    if not image_path or not BLIP_AVAILABLE:
        return ""
    if not _blip_loaded:
        _load_blip()
    if _blip_processor is None or _blip_model is None:
        return ""
    try:
        img = Image.open(image_path).convert("RGB")
        text = f"a studio product photo of a {CAPTION_AUDIENCE}'s {slot_hint or 'clothing item'}"
        inputs = _blip_processor(img, text=text, return_tensors="pt").to(_blip_model.device)
        out = _blip_model.generate(**inputs, max_new_tokens=24)
        cap = _blip_processor.decode(out[0], skip_special_tokens=True)
        return _normalize_caption_gender(cap, CAPTION_AUDIENCE)
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
            pass
        ct._RemainderColsList = _RemainderColsList
except Exception:
    pass
# ---------------------------------------------------------------------

# -----------------------------
# Config (MEN)
# -----------------------------
MODEL_PATH = Path("weather_clothing_recommender.pkl")      # men model
IMAGES_ROOT = Path("clothing_images_men")                  # men image "DB"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "4c703f15e3f9220de836884137342d5d")
REQUEST_TIMEOUT = 10
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# Label sets MUST match folder names under clothing_images_men/
TOP_LABELS = {"shirt", "t-shirt", "kurta", "sweater"}
BOTTOM_LABELS = {"pants", "cotton pants", "shorts"}     # add "jeans" if you make that folder
OUTER_LABELS = {"none", "jacket", "jackets", "coat", "hoodie", "sweater"}

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
# Image "DB" helpers
# -----------------------------
def folder_has_images(label: str) -> bool:
    if (label or "").lower() == "none":
        return True
    p = IMAGES_ROOT / (label or "").lower()
    return p.is_dir() and any(f.suffix.lower() in VALID_EXTS for f in p.iterdir())

def pick_image_for_label(label: str, rng: random.Random) -> Optional[str]:
    if not label or label.lower() == "none":
        return None
    folder = IMAGES_ROOT / label.lower()
    if not folder.is_dir():
        return None
    files = [p for p in folder.iterdir() if p.suffix.lower() in VALID_EXTS]
    if not files:
        return None
    return rng.choice(files).as_posix()

def pick_new_image_same_label(label: str, current_path: Optional[str], rng: random.Random) -> Optional[str]:
    """Keep label fixed; select a different image from the same folder (if possible)."""
    if not label or label.lower() == "none":
        return None
    folder = IMAGES_ROOT / label.lower()
    if not folder.is_dir():
        return current_path
    files = [p.as_posix() for p in folder.iterdir() if p.suffix.lower() in VALID_EXTS]
    if not files:
        return current_path
    options = [f for f in files if f != (current_path or "")]
    return rng.choice(options) if options else current_path

def sanitize_prediction(label: str, slot: str, rng: random.Random) -> str:
    allowed = allowed_labels_for(slot)
    lbl = (label or "").lower()
    if lbl in allowed and folder_has_images(lbl):
        return lbl
    candidates = [x for x in allowed if folder_has_images(x)]
    if not candidates:
        return lbl or ""
    return rng.choice(candidates)

# -----------------------------
# Caption cache
# -----------------------------
def get_caption_for_image(path: Optional[str], cache: Dict[str, str], slot_hint: Optional[str]) -> str:
    if not path or not ENABLE_CAPTIONS:
        return ""
    if path in cache:
        return cache[path]
    cap = generate_caption(path, slot_hint=slot_hint)
    cache[path] = cap
    return cap

# -----------------------------
# Gradio handlers (stateful)
# -----------------------------
def do_recommend(city: str, time_of_day: str, season: str, occasion: str, mood: str, state: Dict):
    weather = fetch_weather(city)
    if weather is None:
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
        "mood": mood,   # men model expects this
    }

    pt, pb, po = predict_outfit(feats)

    seed = random.randint(0, 10_000_000)
    rng = random.Random(seed)

    top    = sanitize_prediction(pt, "top", rng)
    bottom = sanitize_prediction(pb, "bottom", rng)
    outer  = sanitize_prediction(po, "outer", rng)

    state = state or {}
    state["preds"] = {"top": top, "bottom": bottom, "outer": outer}
    state["seed"] = seed

    images = {
        "top":    pick_image_for_label(top, rng),
        "bottom": pick_image_for_label(bottom, rng),
        "outer":  pick_image_for_label(outer, rng)
    }
    state["images"] = images
    state["captions_cache"] = {}

    # captions (label + BLIP if enabled)
    top_cap_model = get_caption_for_image(images["top"], state["captions_cache"], slot_hint="topwear t-shirt, shirt or kurta")
    top_cap = f"Top: {top}" + (f" — {top_cap_model}" if top_cap_model else "")

    bottom_cap_model = get_caption_for_image(images["bottom"], state["captions_cache"], slot_hint="bottomwear pants or shorts")
    bottom_cap = f"Bottom: {bottom}" + (f" — {bottom_cap_model}" if bottom_cap_model else "")

    if outer == "none":
        outer_cap = "Outerwear: None needed"
    else:
        outer_cap_model = get_caption_for_image(images["outer"], state["captions_cache"], slot_hint="outerwear jacket, coat or hoodie")
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
    """Shuffle a new image within the SAME label for the chosen slot."""
    state = state or {}
    preds = state.get("preds") or {}
    images = state.get("images") or {}
    captions_cache = state.get("captions_cache") or {}

    if slot not in {"top", "bottom", "outer"} or not preds.get(slot):
        return (
            gr.update(),
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            state
        )

    seed = state.get("seed", random.randint(0, 10_000_000))
    rng = random.Random(seed)

    label = preds[slot]  # KEEP label fixed
    new_img = pick_new_image_same_label(label, images.get(slot), rng)
    images[slot] = new_img
    state["images"] = images

    # update only the changed slot
    if slot == "top":
        cap_model = get_caption_for_image(images["top"], captions_cache, slot_hint="topwear t-shirt, shirt or kurta")
        cap = f"Top: {label}" + (f" — {cap_model}" if cap_model else "")
        return (
            gr.update(),
            images["top"],  cap,
            gr.update(),    gr.update(),
            gr.update(),    gr.update(),
            state
        )

    if slot == "bottom":
        cap_model = get_caption_for_image(images["bottom"], captions_cache, slot_hint="bottomwear pants or shorts")
        cap = f"Bottom: {label}" + (f" — {cap_model}" if cap_model else "")
        return (
            gr.update(),
            gr.update(),    gr.update(),
            images["bottom"], cap,
            gr.update(),    gr.update(),
            state
        )

    # outer
    if label == "none":
        cap = "Outerwear: None needed"
        return (
            gr.update(),
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            None, cap,
            state
        )
    else:
        cap_model = get_caption_for_image(images["outer"], captions_cache, slot_hint="outerwear jacket, coat or hoodie")
        cap = f"Outerwear: {label}" + (f" — {cap_model}" if cap_model else "")
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
with gr.Blocks(title="WearSmart Men — Outfit Recommender") as demo:
    gr.Markdown("## 👔 WearSmart Men (3-slot image shuffle + captions, single file)")

    with gr.Row():
        city = gr.Textbox(label="City", value="Karachi")
        time_of_day = gr.Dropdown(["morning", "afternoon", "evening", "night"], value="morning", label="Time of Day")
        season = gr.Dropdown(["summer", "winter", "spring", "autumn"], value="summer", label="Season")
        occasion = gr.Dropdown(["casual", "formal", "party", "sports"], value="casual", label="Occasion")
        mood = gr.Dropdown(["good", "neutral", "bad"], value="good", label="Mood")  # required by your model

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
        inputs=[city, time_of_day, season, occasion, mood, state],
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
