# app_gradio_men.py
# Men module — per-slot image shuffle (keeps label), slot-safe labels, MEN-conditioned captions + caption-based Mood Module

import os
import random
import re
import time
from pathlib import Path
from typing import Dict, Tuple, Optional, List
# Add this import at the top
from dynamic_shopping_recommender import generate_dynamic_shopping_recommendations

import gradio as gr
import pandas as pd
import joblib
import requests
from PIL import Image
import csv
from datetime import datetime

# ======================================
# Captioning config (toggle here)
# ======================================
ENABLE_CAPTIONS = True
CAPTION_AUDIENCE = "men"   # used in BLIP prompt normalization (men | women | unisex)

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

# def _load_blip():
#     """Load BLIP (attempt local fine-tune first). Safe no-op if BLIP unavailable."""
#     global _blip_loaded, _blip_processor, _blip_model
#     if _blip_loaded or not BLIP_AVAILABLE:
#         return
#     local_dir = _pick_blip_dir()
#     try:
#         if local_dir is not None:
#             _blip_processor = BlipProcessor.from_pretrained(local_dir.as_posix())
#             _blip_model = BlipForConditionalGeneration.from_pretrained(local_dir.as_posix())
#         else:
#             _blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
#             _blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
#         device = "cuda" if ("torch" in globals() and torch.cuda.is_available()) else "cpu"
#         _blip_model.to(device)
#         _blip_loaded = True
#     except Exception as e:
#         print(f"[BLIP load error] {e}")
#         _blip_loaded = True
#         _blip_processor = None
#         _blip_model = None

def _load_blip():
    """Load fine-tuned or default BLIP model once (safe if unavailable)."""
    global _blip_loaded, _blip_processor, _blip_model
    if _blip_loaded or not BLIP_AVAILABLE:
        return
    try:
        local_dir = Path("blip_finetunedggdata")  # change if your fine-tuned folder name differs
        if local_dir.exists():
            _blip_processor = BlipProcessor.from_pretrained(local_dir.as_posix())
            _blip_model = BlipForConditionalGeneration.from_pretrained(local_dir.as_posix())
        else:
            _blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            _blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _blip_model.to(device)
        _blip_loaded = True
    except Exception as e:
        print(f"[BLIP load error] {e}")
        _blip_loaded = True
        _blip_processor = _blip_model = None


def _normalize_caption_gender(cap: str, audience: str) -> str:
    """Small search/replace to normalize gendered wording in captions to audience."""
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
    """Generate a short BLIP caption for a given image path (returns empty on failure)."""
    if not image_path or not BLIP_AVAILABLE:
        return ""
    if not _blip_loaded:
        _load_blip()
    if _blip_processor is None or _blip_model is None:
        return ""
    try:
        img = Image.open(image_path).convert("RGB")
        # Provide a small prompt context to encourage fashion-related phrasing
        text = f"a studio product photo of a {CAPTION_AUDIENCE}'s {slot_hint or 'clothing item'}"
        inputs = _blip_processor(img, text=text, return_tensors="pt").to(_blip_model.device)
        out = _blip_model.generate(**inputs, max_new_tokens=24)
        cap = _blip_processor.decode(out[0], skip_special_tokens=True)
        return _normalize_caption_gender(cap, CAPTION_AUDIENCE)
    except Exception as e:
        print(f"[BLIP caption error] {e}")
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
MODEL_PATH = Path("weather_clothing_recommender.pkl")      # men model (your file)
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

def predict_outfit(features: Dict):
    df = pd.DataFrame([features])
    if 'mood' not in df.columns:
        df['mood'] = 'Neutral'  # default placeholder for models expecting mood
    pred_top, pred_bottom, pred_outer = _model.predict(df)[0]
    return pred_top, pred_bottom, pred_outer

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
# Color extraction + aliases (copied from female module)
# -----------------------------
COLOR_NAMES = [
    "red", "green", "blue", "yellow", "orange", "purple", "pink",
    "brown", "black", "white", "gray", "beige", "maroon", "navy",
    "teal", "cyan", "gold", "silver", "cream"
]

COLOR_ALIASES = {
    # --- Gray / Grey ---
    "grey": "gray",
    "charcoal": "gray",
    "slate": "gray",
    "ash": "gray",
    "smoke": "gray",
    "graphite": "gray",
    "silver": "gray",
    "gunmetal": "gray",
    "pewter": "gray",

    # --- Blue ---
    "sky": "blue",
    "navy": "blue",
    "teal": "blue",
    "turquoise": "blue",
    "aqua": "blue",
    "azure": "blue",
    "babyblue": "blue",
    "cobalt": "blue",
    "indigo": "blue",
    "royalblue": "blue",
    "denim": "blue",
    "sapphire": "blue",
    "midnight": "blue",

    # --- Red ---
    "crimson": "red",
    "scarlet": "red",
    "ruby": "red",
    "cherry": "red",
    "garnet": "red",
    "blood": "red",
    "rosewood": "red",
    "rust": "red",
    "wine": "red",
    "brick": "red",
    "mahogany": "red",

    # --- Maroon / Burgundy ---
    "burgundy": "maroon",
    "oxblood": "maroon",
    "berry": "maroon",
    "plum": "maroon",
    "raisin": "maroon",

    # --- Green ---
    "lime": "green",
    "olive": "green",
    "forest": "green",
    "emerald": "green",
    "mint": "green",
    "sage": "green",
    "moss": "green",
    "seafoam": "green",
    "jade": "green",
    "chartreuse": "green",
    "avocado": "green",
    "basil": "green",

    # --- Yellow / Gold ---
    "golden": "gold",
    "mustard": "yellow",
    "lemon": "yellow",
    "amber": "yellow",
    "honey": "yellow",
    "canary": "yellow",
    "sunflower": "yellow",
    "beige": "yellow",
    "sand": "yellow",
    "camel": "yellow",
    "khaki": "yellow",
    "tan": "yellow",

    # --- Orange ---
    "apricot": "orange",
    "peach": "orange",
    "tangerine": "orange",
    "coral": "orange",
    "salmon": "orange",
    "terracotta": "orange",
    "rusty": "orange",
    "pumpkin": "orange",

    # --- Purple / Violet ---
    "violet": "purple",
    "lavender": "purple",
    "lilac": "purple",
    "mauve": "purple",
    "orchid": "purple",
    "amethyst": "purple",
    "magenta": "purple",
    "eggplant": "purple",

    # --- Pink ---
    "rose": "pink",
    "blush": "pink",
    "fuchsia": "pink",
    "hotpink": "pink",
    "salmonpink": "pink",
    "baby pink": "pink",
    "bubblegum": "pink",
    "coralpink": "pink",
    "peony": "pink",
    "dustyrose": "pink",

    # --- Brown ---
    "chocolate": "brown",
    "coffee": "brown",
    "mocha": "brown",
    "walnut": "brown",
    "caramel": "brown",
    "bronze": "brown",
    "copper": "brown",
    "espresso": "brown",
    "rustbrown": "brown",
    "hazel": "brown",

    # --- White / Cream ---
    "offwhite": "white",
    "off-white": "white",
    "ivory": "white",
    "cream": "white",
    "eggshell": "white",
    "snow": "white",
    "pearl": "white",
    "linen": "white",
    "porcelain": "white",

    # --- Black ---
    "jet": "black",
    "onyx": "black",
    "ebony": "black",
    "coal": "black",
    "ink": "black",
    "char": "black",
    "graphiteblack": "black",

    # --- Metallics ---
    "platinum": "silver",
    "chrome": "silver",
    "metallic": "silver",
    "steel": "silver",

    # --- Others / Misc Fashion Shades ---
    "mintgreen": "green",
    "dustyblue": "blue",
    "pastelpink": "pink",
    "pastelyellow": "yellow",
    "creamwhite": "white",
    "sandstone": "beige",
    "camelbrown": "brown",
    "copperred": "red",
    "taupe": "beige",
    "beigebrown": "brown",
    "offgray": "gray"
}

def normalize_color_word(word: str) -> str:
    w = (word or "").strip().lower()
    return COLOR_ALIASES.get(w, w)

def extract_color_from_caption(caption: str) -> Optional[str]:
    """Return first matched color name (canonicalized) or None."""
    if not caption:
        return None
    text = caption.lower()
    # Try exact known color words first (word boundaries)
    for c in COLOR_NAMES:
        if re.search(rf"\b{re.escape(c)}\b", text):
            return c
    # Try aliases
    for alias, canonical in COLOR_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return canonical
    return None

# -----------------------------
# Caption cache (global, in-memory)
# -----------------------------
_caption_cache: Dict[str, str] = {}  # image_path -> caption_lower

def get_blip_caption_cached(image_path: Optional[str]) -> str:
    """Return a lowercased caption for image_path, caching results."""
    if not image_path:
        return ""
    if image_path in _caption_cache:
        return _caption_cache[image_path]
    caption = generate_caption(image_path) or ""
    caption_l = caption.lower().strip()
    _caption_cache[image_path] = caption_l
    return caption_l

def precompute_captions_for_label(label: str, progress_callback: Optional[callable] = None):
    """Generate & cache captions for all images in the label folder."""
    if not label or label.lower() == "none":
        return
    folder = IMAGES_ROOT / label.lower()
    if not folder.exists():
        return
    files = [p for p in folder.iterdir() if p.suffix.lower() in VALID_EXTS]
    total = len(files)
    for i, p in enumerate(files, start=1):
        get_blip_caption_cached(str(p))
        if progress_callback:
            progress_callback(i, total)

# -----------------------------
# Weather-based recommendation + BLIP caption & color display
# -----------------------------
def do_recommend(city: str, time_of_day: str, season: str, occasion: str, state: Dict):
    weather = fetch_weather(city)
    if not weather:
        return (
            "❌ Failed to fetch weather.",
            gr.update(), "Top: (unchanged)",
            gr.update(), "Bottom: (unchanged)",
            gr.update(), "Outerwear: (unchanged)",
            state or {}
        )

    # ✅ FORMAL OCCASION OVERRIDE
    if occasion.lower() == "formal":
        seed = random.randint(0, 10_000_000)
        rng = random.Random(seed)
        
        # Force formal clothing
        top = "formal_shirts"
        bottom = "formal_pants"
        outer = "coat"
        
        images = {
            "top": pick_image_for_label(top, rng),
            "bottom": pick_image_for_label(bottom, rng),
            "outer": pick_image_for_label(outer, rng),
        }

        captions = {
            slot: get_blip_caption_cached(path) if path else ""
            for slot, path in images.items()
        }

        state = {
            "preds": {"top": top, "bottom": bottom, "outer": outer},
            "images": images,
            "captions": captions,
            "seed": seed,
        }

        weather_text = (
            f"🌤️ {weather['weather_condition'].capitalize()} | 🌡️ {weather['temperature']}°C "
            f"(feels {weather['feels_like']}°C) | 💧 {weather['humidity']}% | 💨 {weather['wind_speed']} m/s\n"
            f"**👔 Formal attire selected**"
        )

        return (
            weather_text,
            images["top"], f"👕 Top: {top}\n📝 {captions['top'] or 'No caption'}",
            images["bottom"], f"👖 Bottom: {bottom}\n📝 {captions['bottom'] or 'No caption'}",
            images["outer"], f"🧥 Outerwear: {outer}\n📝 {captions['outer'] or 'No caption'}",
            state
        )

    # ✅ CONTINUE WITH NORMAL MODEL PREDICTION FOR OTHER OCCASIONS
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

    pt, pb, po = predict_outfit(feats)
    seed = random.randint(0, 10_000_000)
    rng = random.Random(seed)

    top = sanitize_prediction(pt, "top", rng)
    bottom = sanitize_prediction(pb, "bottom", rng)
    outer = sanitize_prediction(po, "outer", rng)

    images = {
        "top": pick_image_for_label(top, rng),
        "bottom": pick_image_for_label(bottom, rng),
        "outer": pick_image_for_label(outer, rng),
    }

    captions = {
        slot: get_blip_caption_cached(path) if path else ""
        for slot, path in images.items()
    }

    state = {
        "preds": {"top": top, "bottom": bottom, "outer": outer},
        "images": images,
        "captions": captions,
        "seed": seed,
    }

    weather_text = (
        f"🌤️ {weather['weather_condition'].capitalize()} | 🌡️ {weather['temperature']}°C "
        f"(feels {weather['feels_like']}°C) | 💧 {weather['humidity']}% | 💨 {weather['wind_speed']} m/s"
    )

    return (
        weather_text,
        images["top"], f"👕 Top: {top}\n📝 {captions['top'] or 'No caption'}",
        images["bottom"], f"👖 Bottom: {bottom}\n📝 {captions['bottom'] or 'No caption'}",
        images["outer"], f"🧥 Outerwear: {outer if outer != 'none' else 'None'}\n📝 {captions['outer'] or 'No caption'}",
        state
    )
# -----------------------------
# Mood Module (caption-based color filtering)
# -----------------------------
def filter_images_by_color_using_captions(color: str, label: str) -> List[str]:
    """Scan all images in label folder, generate captions, extract colors from captions, and return matches."""
    if not color or not label or label.lower() == "none":
        return []
    folder = IMAGES_ROOT / label.lower()
    if not folder.exists():
        return []

    requested = normalize_and_canonicalize_color_input(color)
    matches: List[str] = []

    # Precompute captions for all images in label
    precompute_captions_for_label(label)

    for p in folder.iterdir():
        if p.suffix.lower() not in VALID_EXTS:
            continue
        img_path = str(p)
        cap = _caption_cache.get(img_path, "")  # lowercased caption
        if not cap:
            continue

        # 1) Direct word match (alias-aware)
        if re.search(rf"\b{re.escape(requested)}\b", cap):
            matches.append(img_path)
            continue

        # 2) Check detected color from caption
        det = extract_color_from_caption(cap)
        if det and normalize_and_canonicalize_color_input(det) == requested:
            matches.append(img_path)
            continue

        # 3) Substring fallback — match 'navy' when user typed 'blue' if caption contains both
        if requested in cap:
            matches.append(img_path)
            continue

    return matches

def normalize_and_canonicalize_color_input(color: str) -> str:
    c = (color or "").strip().lower()
    if not c:
        return c
    c = normalize_color_word(c)
    return c

def filter_images_by_color_filename_fallback(color: str, label: str) -> List[str]:
    """Fallback: search filenames for normalized color token."""
    if not color or not label or label.lower() == "none":
        return []
    folder = IMAGES_ROOT / label.lower()
    if not folder.exists():
        return []
    tok = normalize_and_canonicalize_color_input(color)
    return [
        str(p) for p in folder.iterdir()
        if p.suffix.lower() in VALID_EXTS and tok in p.name.lower()
    ]

def do_color_filter(top_color, bottom_color, outer_color, state):
    """Gradio handler: uses BLIP captions to find color matches across all images in predicted label folders."""
    state = state or {}
    preds = state.get("preds", {})
    top_label = preds.get("top")
    bottom_label = preds.get("bottom")
    outer_label = preds.get("outer")

    top_matches = []
    bottom_matches = []
    outer_matches = []

    # Top
    if top_color and top_label:
        if BLIP_AVAILABLE:
            top_matches = filter_images_by_color_using_captions(top_color, top_label)
        else:
            top_matches = filter_images_by_color_filename_fallback(top_color, top_label)

    # Bottom
    if bottom_color and bottom_label:
        if BLIP_AVAILABLE:
            bottom_matches = filter_images_by_color_using_captions(bottom_color, bottom_label)
        else:
            bottom_matches = filter_images_by_color_filename_fallback(bottom_color, bottom_label)

    # Outer
    if outer_color and outer_label and outer_label.lower() != "none":
        if BLIP_AVAILABLE:
            outer_matches = filter_images_by_color_using_captions(outer_color, outer_label)
        else:
            outer_matches = filter_images_by_color_filename_fallback(outer_color, outer_label)

    # If no matches found, return friendly message
    if not any([top_matches, bottom_matches, outer_matches]):
        return (
            "⚠️ No matches found. Try synonyms (e.g., 'grey'/'gray', 'navy', 'beige') or precompute captions for your dataset.",
            [], "", [], "", [], "", state
        )

    top_caption = f"Top ({top_label}) — {top_color or 'N/A'} — {len(top_matches)} match(es)" if top_label else ""
    bottom_caption = f"Bottom ({bottom_label}) — {bottom_color or 'N/A'} — {len(bottom_matches)} match(es)" if bottom_label else ""
    outer_caption = f"Outerwear ({outer_label}) — {outer_color or 'N/A'} — {len(outer_matches)} match(es)" if outer_label else ""

    return (
        "🎨 Showing color-filtered matches (caption-based):",
        top_matches, top_caption,
        bottom_matches, bottom_caption,
        outer_matches, outer_caption,
        state
    )

def get_caption_for_image(image_path: Optional[str], captions_cache: Dict[str, str], slot_hint: Optional[str] = None) -> str:
    """Get a caption for an image, using cache if available; otherwise generate and cache it."""
    if not image_path:
        return ""
    if image_path in captions_cache:
        return captions_cache[image_path]

    caption = generate_caption(image_path, slot_hint=slot_hint) or ""
    caption_l = caption.strip()
    captions_cache[image_path] = caption_l
    return caption_l


# -----------------------------
# Reroll (keeps label fixed, shuffle images)
# -----------------------------
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
# Add this new function after the do_reroll function (around line 580)

def do_override_selection(top_override, bottom_override, outer_override, state):
    """Allow user to manually override the recommended clothing items."""
    state = state or {}
    preds = state.get("preds", {})
    images = state.get("images", {})
    captions = state.get("captions", {})
    
    if not preds:
        return (
            "⚠️ Please get a recommendation first!",
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            state
        )
    
    seed = state.get("seed", random.randint(0, 10_000_000))
    rng = random.Random(seed)
    
    # Map display names to folder names
    folder_mapping = {
        "formal_shirts": "formal_shirts",
        "formal_pants": "formal_pants",
        "t-shirt": "t-shirt",
        "shirt": "shirt",
        "kurta": "kurta",
        "sweater": "sweater",
        "pants": "pants",
        "cotton pants": "cotton pants",
        "jeans": "jeans",
        "shorts": "shorts",
        "trousers": "trousers",
        "coat": "coat",
        "hoodie": "hoodie",
        "jackets": "jackets",
        "none": "none"
    }
    
    # Update predictions based on user overrides
    if top_override and top_override != "-- Keep Recommendation --":
        folder_name = folder_mapping.get(top_override.lower(), top_override.lower())
        preds["top"] = folder_name
        images["top"] = pick_image_for_label(folder_name, rng)
        captions["top"] = get_blip_caption_cached(images["top"]) if images["top"] else ""
    
    if bottom_override and bottom_override != "-- Keep Recommendation --":
        folder_name = folder_mapping.get(bottom_override.lower(), bottom_override.lower())
        preds["bottom"] = folder_name
        images["bottom"] = pick_image_for_label(folder_name, rng)
        captions["bottom"] = get_blip_caption_cached(images["bottom"]) if images["bottom"] else ""
    
    if outer_override and outer_override != "-- Keep Recommendation --":
        folder_name = folder_mapping.get(outer_override.lower(), outer_override.lower())
        preds["outer"] = folder_name
        images["outer"] = pick_image_for_label(folder_name, rng)
        captions["outer"] = get_blip_caption_cached(images["outer"]) if images["outer"] else ""
    
    # Update state
    state["preds"] = preds
    state["images"] = images
    state["captions"] = captions
    
    # Prepare captions for display
    top_label = preds.get("top", "")
    bottom_label = preds.get("bottom", "")
    outer_label = preds.get("outer", "")
    
    top_caption = f"👕 Top: {top_label}\n📝 {captions.get('top', 'No caption')}"
    bottom_caption = f"👖 Bottom: {bottom_label}\n📝 {captions.get('bottom', 'No caption')}"
    outer_caption = f"🧥 Outerwear: {outer_label if outer_label != 'none' else 'None'}\n📝 {captions.get('outer', 'No caption')}"
    
    return (
        "✅ Outfit updated with your preferences!",
        images.get("top"), top_caption,
        images.get("bottom"), bottom_caption,
        images.get("outer"), outer_caption,
        state
    )

# Add this function before the Gradio UI
def show_shopping_recommendations_with_pref(state, pref_cat):
    """Show dynamic shopping recommendations (web data) with optional preferred category."""
    state = state or {}
    season = state.get("season", "summer")
    caption_cache = state.get("captions", {})
    
    wardrobe_summary, gap_analysis, shopping_list, product_images, product_links = generate_dynamic_shopping_recommendations(
        images_root=str(IMAGES_ROOT),
        season=season,
        caption_cache=caption_cache,
        gender="men",
        preferred_category=pref_cat or ""
    )
    
    # Format product links for display
    links_display = "### 🔗 **Purchase Links**\n\n"
    if product_links:
        for i, link in enumerate(product_links, 1):
            links_display += f"{i}. [Product {i}]({link})\n"
    else:
        links_display += "No product links available at the moment."
    
    return wardrobe_summary, gap_analysis, shopping_list, product_images, links_display

def _append_feedback_csv(file_path: str, payload: Dict[str, str]):
    """Append a single feedback row to CSV, creating headers if file is new."""
    file_exists = os.path.exists(file_path)
    fieldnames = [
        "timestamp", "gender", "city", "season", "occasion",
        "top_label", "bottom_label", "outer_label",
        "liked", "source"
    ]
    with open(file_path, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(payload)

def on_feedback(liked: bool, state: Dict) -> str:
    """Gradio handler to persist feedback for current recommendation."""
    st = state or {}
    preds = (st.get("preds") or {})
    meta_city = st.get("city", "")
    meta_season = st.get("season", "")
    meta_occasion = st.get("occasion", "")
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "gender": "male",
        "city": meta_city,
        "season": meta_season,
        "occasion": meta_occasion,
        "top_label": preds.get("top", ""),
        "bottom_label": preds.get("bottom", ""),
        "outer_label": preds.get("outer", ""),
        "liked": "yes" if liked else "no",
        "source": "shopping_recommendation"
    }
    _append_feedback_csv("feedback_log.csv", payload)
    return "✅ Thanks for your feedback!"
# Now update the UI section (replace the existing UI code starting from line ~585)

with gr.Blocks(title="WearSmart Men — Weather + BLIP + Mood Module") as demo:
    gr.Markdown("## 👔 WearSmart Men — Weather + BLIP Captions + Caption-based Mood Module")

    with gr.Row():
        city = gr.Textbox(label="City", value="Karachi")
        time_of_day = gr.Dropdown(["morning", "afternoon", "evening", "night"], value="morning")
        season = gr.Dropdown(["summer", "winter", "spring", "autumn"], value="summer")
        occasion = gr.Dropdown(["casual", "formal", "party", "sports"], value="casual")

    state = gr.State({})

    recommend_btn = gr.Button("💡 Recommend Outfit", variant="primary")
    weather_box = gr.Markdown()

    # Add Override Dropdowns
    gr.Markdown("### 🔄 Want to change the recommendation? Select different items below:")
    with gr.Row():
        top_dropdown = gr.Dropdown(
            choices=["-- Keep Recommendation --"] + sorted([x.title() for x in TOP_LABELS]),
            value="-- Keep Recommendation --",
            label="Override Top"
        )
        bottom_dropdown = gr.Dropdown(
            choices=["-- Keep Recommendation --"] + sorted([x.title() for x in BOTTOM_LABELS]),
            value="-- Keep Recommendation --",
            label="Override Bottom"
        )
        outer_dropdown = gr.Dropdown(
            choices=["-- Keep Recommendation --"] + sorted([x.title() for x in OUTER_LABELS]),
            value="-- Keep Recommendation --",
            label="Override Outerwear"
        )
    
    override_btn = gr.Button("✨ Apply My Choices", variant="secondary")

    with gr.Row():
        top_img = gr.Image(label="Top", type="filepath")
        top_cap = gr.Markdown()
    with gr.Row():
        bottom_img = gr.Image(label="Bottom", type="filepath")
        bottom_cap = gr.Markdown()
    with gr.Row():
        outer_img = gr.Image(label="Outerwear", type="filepath")
        outer_cap = gr.Markdown()

    recommend_btn.click(
        fn=do_recommend,
        inputs=[city, time_of_day, season, occasion, state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state],
    )

    override_btn.click(
        fn=do_override_selection,
        inputs=[top_dropdown, bottom_dropdown, outer_dropdown, state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state],
    )

    with gr.Row():
        reroll_top = gr.Button("🔁 Reroll Top")
        reroll_bottom = gr.Button("🔁 Reroll Bottom")
        reroll_outer = gr.Button("🔁 Reroll Outerwear")

    reroll_top.click(lambda s: do_reroll("top", s),
        inputs=[state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state])
    reroll_bottom.click(lambda s: do_reroll("bottom", s),
        inputs=[state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state])
    reroll_outer.click(lambda s: do_reroll("outer", s),
        inputs=[state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state])

    gr.Markdown("---")
    gr.Markdown("## 🎨 Mood Module — Filter by Your Favorite Colors (caption-based)")

    with gr.Row():
        top_color = gr.Textbox(label="Preferred color for Top (e.g., blue, green, navy)")
        bottom_color = gr.Textbox(label="Preferred color for Bottom")
        outer_color = gr.Textbox(label="Preferred color for Outerwear (optional)")

    mood_btn = gr.Button("🎨 Show Outfits in My Colors", variant="secondary")
    mood_info = gr.Markdown()

    with gr.Row():
        mood_top_gallery = gr.Gallery(label="Top Matches", columns=3, height="auto")
        mood_top_cap = gr.Markdown()
    with gr.Row():
        mood_bottom_gallery = gr.Gallery(label="Bottom Matches", columns=3, height="auto")
        mood_bottom_cap = gr.Markdown()
    with gr.Row():
        mood_outer_gallery = gr.Gallery(label="Outerwear Matches", columns=3, height="auto")
        mood_outer_cap = gr.Markdown()

    mood_btn.click(
        fn=do_color_filter,
        inputs=[top_color, bottom_color, outer_color, state],
        outputs=[
            mood_info,
            mood_top_gallery, mood_top_cap,
            mood_bottom_gallery, mood_bottom_cap,
            mood_outer_gallery, mood_outer_cap,
            state,
        ]
    )

    # Optional: Button to precompute captions for predicted folders
    def precompute_for_current(state):
        st = state or {}
        preds = st.get("preds", {})
        labels = [preds.get("top"), preds.get("bottom"), preds.get("outer")]
        for lbl in labels:
            if lbl and lbl.lower() != "none":
                precompute_captions_for_label(lbl)
        return "✅ Captions precomputed for current predicted folders.", state

    precompute_btn = gr.Button("🗂️ Precompute captions for current predicted folders")
    precompute_res = gr.Markdown()
    precompute_btn.click(fn=precompute_for_current, inputs=[state], outputs=[precompute_res, state])
    
        # Add Shopping Recommendations Tab
    gr.Markdown("---")
    gr.Markdown("## 🛍️ Future Shopping Recommendations")
    
    with gr.Row():
        preferred_category = gr.Dropdown(
            label="Preferred category (optional)",
            choices=[
                "", "Shirt", "T-Shirt", "Kurta", "Sweater",
                "Jeans", "Trousers", "Pants", "Shorts",
                "Jacket", "Coat", "Hoodie"
            ],
            value=""
        )
        shopping_btn = gr.Button("🛍️ Analyze My Wardrobe & Get Shopping List", variant="primary", size="lg")
    
    with gr.Row():
        with gr.Column():
            wardrobe_summary = gr.Markdown(label="Current Wardrobe")
        with gr.Column():
            gap_analysis = gr.Markdown(label="Gap Analysis")
    
    shopping_list = gr.Markdown(label="Shopping Recommendations")
    
    # Product images gallery
    gr.Markdown("### 🖼️ Recommended Products")
    product_gallery = gr.Gallery(label="Product Images", columns=3, height="auto")
    
    # Product links
    gr.Markdown("### 🔗 Product Links")
    product_links_display = gr.Markdown(label="Purchase Links")
    
    shopping_btn.click(
        fn=show_shopping_recommendations_with_pref,
        inputs=[state, preferred_category],
        outputs=[wardrobe_summary, gap_analysis, shopping_list, product_gallery, product_links_display]
    )

    with gr.Row():
        like_btn = gr.Button("👍 I like this recommendation", variant="secondary")
        dislike_btn = gr.Button("👎 I don't like this recommendation", variant="secondary")
    feedback_status = gr.Markdown()

    like_btn.click(
        fn=lambda s: on_feedback(True, s),
        inputs=[state],
        outputs=[feedback_status]
    )
    dislike_btn.click(
        fn=lambda s: on_feedback(False, s),
        inputs=[state],
        outputs=[feedback_status]
    )

if __name__ == "__main__":
    demo.launch()