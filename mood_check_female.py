


# # app_gradio.py
# # ✅ AI Outfit Recommender with Weather + BLIP Captioning + Color Detection + Mood Module
# # app_gradio.py
# # AI Outfit Recommender — Weather + BLIP captioning + Mood Module (caption-based color filtering)

# import os
# import random
# from pathlib import Path
# from typing import Dict, Tuple, Optional, List
# import gradio as gr
# import pandas as pd
# import joblib
# import requests
# from PIL import Image
# import re
# import json
# import time

# # ==========================
# # BLIP Captioning Setup
# # ==========================
# BLIP_AVAILABLE = True
# try:
#     import torch
#     from transformers import BlipProcessor, BlipForConditionalGeneration
# except Exception:
#     BLIP_AVAILABLE = False
#     BlipProcessor = BlipForConditionalGeneration = None

# _blip_loaded = False
# _blip_processor = None
# _blip_model = None

# def _load_blip():
#     """Load fine-tuned or default BLIP model once (safe if unavailable)."""
#     global _blip_loaded, _blip_processor, _blip_model
#     if _blip_loaded or not BLIP_AVAILABLE:
#         return
#     try:
#         local_dir = Path("blip_finetunedggdata")  # change if your fine-tuned folder name differs
#         if local_dir.exists():
#             _blip_processor = BlipProcessor.from_pretrained(local_dir.as_posix())
#             _blip_model = BlipForConditionalGeneration.from_pretrained(local_dir.as_posix())
#         else:
#             _blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
#             _blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
#         device = "cuda" if torch.cuda.is_available() else "cpu"
#         _blip_model.to(device)
#         _blip_loaded = True
#     except Exception as e:
#         print(f"[BLIP load error] {e}")
#         _blip_loaded = True
#         _blip_processor = _blip_model = None

# def generate_caption(image_path: Optional[str]) -> str:
#     """Generate caption for an image using BLIP. Returns empty string on failure."""
#     if not image_path or not BLIP_AVAILABLE:
#         return ""
#     if not _blip_loaded:
#         _load_blip()
#     if not _blip_model or not _blip_processor:
#         return ""
#     try:
#         img = Image.open(image_path).convert("RGB")
#         inputs = _blip_processor(img, return_tensors="pt").to(_blip_model.device)
#         out = _blip_model.generate(**inputs, max_new_tokens=24)
#         caption = _blip_processor.decode(out[0], skip_special_tokens=True)
#         return caption
#     except Exception as e:
#         print(f"[BLIP caption error] {e}")
#         return ""

# # ==========================
# # Color extraction + aliases
# # ==========================
# COLOR_NAMES = [
#     "red", "green", "blue", "yellow", "orange", "purple", "pink",
#     "brown", "black", "white", "gray", "beige", "maroon", "navy",
#     "teal", "cyan", "gold", "silver", "cream"
# ]

# COLOR_ALIASES = {
#     # --- Gray / Grey ---
#     "grey": "gray",
#     "charcoal": "gray",
#     "slate": "gray",
#     "ash": "gray",
#     "smoke": "gray",
#     "graphite": "gray",
#     "silver": "gray",
#     "gunmetal": "gray",
#     "pewter": "gray",

#     # --- Blue ---
#     "sky": "blue",
#     "navy": "blue",
#     "teal": "blue",
#     "turquoise": "blue",
#     "aqua": "blue",
#     "azure": "blue",
#     "babyblue": "blue",
#     "cobalt": "blue",
#     "indigo": "blue",
#     "royalblue": "blue",
#     "denim": "blue",
#     "sapphire": "blue",
#     "midnight": "blue",

#     # --- Red ---
#     "crimson": "red",
#     "scarlet": "red",
#     "ruby": "red",
#     "cherry": "red",
#     "garnet": "red",
#     "blood": "red",
#     "rosewood": "red",
#     "rust": "red",
#     "wine": "red",
#     "brick": "red",
#     "mahogany": "red",

#     # --- Maroon / Burgundy ---
#     "burgundy": "maroon",
#     "oxblood": "maroon",
#     "berry": "maroon",
#     "plum": "maroon",
#     "raisin": "maroon",

#     # --- Green ---
#     "lime": "green",
#     "olive": "green",
#     "forest": "green",
#     "emerald": "green",
#     "mint": "green",
#     "sage": "green",
#     "moss": "green",
#     "seafoam": "green",
#     "jade": "green",
#     "chartreuse": "green",
#     "avocado": "green",
#     "basil": "green",

#     # --- Yellow / Gold ---
#     "golden": "gold",
#     "mustard": "yellow",
#     "lemon": "yellow",
#     "amber": "yellow",
#     "honey": "yellow",
#     "canary": "yellow",
#     "sunflower": "yellow",
#     "beige": "yellow",
#     "sand": "yellow",
#     "camel": "yellow",
#     "khaki": "yellow",
#     "tan": "yellow",

#     # --- Orange ---
#     "apricot": "orange",
#     "peach": "orange",
#     "tangerine": "orange",
#     "coral": "orange",
#     "salmon": "orange",
#     "terracotta": "orange",
#     "rusty": "orange",
#     "pumpkin": "orange",

#     # --- Purple / Violet ---
#     "violet": "purple",
#     "lavender": "purple",
#     "lilac": "purple",
#     "mauve": "purple",
#     "orchid": "purple",
#     "amethyst": "purple",
#     "magenta": "purple",
#     "eggplant": "purple",

#     # --- Pink ---
#     "rose": "pink",
#     "blush": "pink",
#     "fuchsia": "pink",
#     "hotpink": "pink",
#     "salmonpink": "pink",
#     "baby pink": "pink",
#     "bubblegum": "pink",
#     "coralpink": "pink",
#     "peony": "pink",
#     "dustyrose": "pink",

#     # --- Brown ---
#     "chocolate": "brown",
#     "coffee": "brown",
#     "mocha": "brown",
#     "walnut": "brown",
#     "caramel": "brown",
#     "bronze": "brown",
#     "copper": "brown",
#     "espresso": "brown",
#     "rustbrown": "brown",
#     "hazel": "brown",

#     # --- White / Cream ---
#     "offwhite": "white",
#     "off-white": "white",
#     "ivory": "white",
#     "cream": "white",
#     "eggshell": "white",
#     "snow": "white",
#     "pearl": "white",
#     "linen": "white",
#     "porcelain": "white",

#     # --- Black ---
#     "jet": "black",
#     "onyx": "black",
#     "ebony": "black",
#     "coal": "black",
#     "ink": "black",
#     "char": "black",
#     "graphiteblack": "black",

#     # --- Metallics ---
#     "platinum": "silver",
#     "chrome": "silver",
#     "metallic": "silver",
#     "steel": "silver",

#     # --- Others / Misc Fashion Shades ---
#     "mintgreen": "green",
#     "dustyblue": "blue",
#     "pastelpink": "pink",
#     "pastelyellow": "yellow",
#     "creamwhite": "white",
#     "sandstone": "beige",
#     "camelbrown": "brown",
#     "copperred": "red",
#     "taupe": "beige",
#     "beigebrown": "brown",
#     "offgray": "gray"
# }


# def normalize_color_word(word: str) -> str:
#     w = (word or "").strip().lower()
#     return COLOR_ALIASES.get(w, w)

# def extract_color_from_caption(caption: str) -> Optional[str]:
#     """Return first matched color name (canonicalized) or None."""
#     if not caption:
#         return None
#     text = caption.lower()
#     # Try to find exact known color words first (word boundaries)
#     for c in COLOR_NAMES:
#         if re.search(rf"\b{re.escape(c)}\b", text):
#             return c
#     # Try aliases
#     for alias, canonical in COLOR_ALIASES.items():
#         if re.search(rf"\b{re.escape(alias)}\b", text):
#             return canonical
#     return None

# # ==========================
# # Config
# # ==========================
# MODEL_PATH = Path("weather_clothing_recommender_women.pkl")
# IMAGES_ROOT = Path("clothing_images")
# OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "4c703f15e3f9220de836884137342d5d")
# REQUEST_TIMEOUT = 10

# TOP_LABELS = {"tops", "shirts", "kurtas"}
# BOTTOM_LABELS = {"trousers", "jeans", "leggings", "capris"}
# OUTER_LABELS = {"none", "coat", "jacket", "puffer_jacket", "dupatta"}

# def allowed_labels_for(slot: str) -> set:
#     if slot == "top":
#         return {x.lower() for x in TOP_LABELS}
#     if slot == "bottom":
#         return {x.lower() for x in BOTTOM_LABELS}
#     return {x.lower() for x in OUTER_LABELS}

# # ==========================
# # Weather fetch
# # ==========================
# def fetch_weather(city: str) -> Optional[Dict]:
#     if not city:
#         return None
#     try:
#         url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
#         r = requests.get(url, timeout=REQUEST_TIMEOUT)
#         if r.status_code != 200:
#             return None
#         d = r.json()
#         return {
#             "temperature": d["main"]["temp"],
#             "feels_like": d["main"]["feels_like"],
#             "humidity": d["main"]["humidity"],
#             "wind_speed": d["wind"]["speed"],
#             "weather_condition": d["weather"][0]["main"].lower(),
#         }
#     except Exception:
#         return None

# # ==========================
# # Model load
# # ==========================
# if not MODEL_PATH.exists():
#     raise FileNotFoundError(f"Model not found: {MODEL_PATH.resolve()}")
# _model = joblib.load(MODEL_PATH.as_posix())

# def predict_outfit(features: Dict) -> Tuple[str, str, str]:
#     df = pd.DataFrame([features])
#     return _model.predict(df)[0]

# # ==========================
# # Image utils
# # ==========================
# VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# def folder_has_images(label: str) -> bool:
#     if (label or "").lower() == "none":
#         return True
#     p = IMAGES_ROOT / (label or "").lower()
#     return p.is_dir() and any(f.suffix.lower() in VALID_EXTS for f in p.iterdir())

# def pick_image_for_label(label: str, rng: random.Random) -> Optional[str]:
#     if label is None or label.lower() == "none":
#         return None
#     folder = IMAGES_ROOT / label.lower()
#     if not folder.is_dir():
#         return None
#     files = [p for p in folder.iterdir() if p.suffix.lower() in VALID_EXTS]
#     return rng.choice(files).as_posix() if files else None

# def sanitize_prediction(label: str, slot: str, rng: random.Random) -> str:
#     allowed = allowed_labels_for(slot)
#     lbl = (label or "").lower()
#     if lbl in allowed and folder_has_images(lbl):
#         return lbl
#     candidates = [x for x in allowed if folder_has_images(x)]
#     return rng.choice(candidates) if candidates else lbl or ""

# # ==========================
# # Caption cache (in-memory)
# # ==========================
# _caption_cache: Dict[str, str] = {}  # image_path -> caption_lower

# def get_blip_caption_cached(image_path: str) -> str:
#     """Return a lowercased caption for image_path, caching results."""
#     if not image_path:
#         return ""
#     if image_path in _caption_cache:
#         return _caption_cache[image_path]
#     caption = generate_caption(image_path) or ""
#     caption_l = caption.lower().strip()
#     _caption_cache[image_path] = caption_l
#     return caption_l

# def precompute_captions_for_label(label: str, progress_callback: Optional[callable] = None):
#     """Generate & cache captions for all images in the label folder."""
#     if not label or label.lower() == "none":
#         return
#     folder = IMAGES_ROOT / label.lower()
#     if not folder.exists():
#         return
#     files = [p for p in folder.iterdir() if p.suffix.lower() in VALID_EXTS]
#     total = len(files)
#     for i, p in enumerate(files, start=1):
#         get_blip_caption_cached(str(p))
#         if progress_callback:
#             # optional: call back to UI progress
#             progress_callback(i, total)

# # ==========================
# # Weather-based recommendation + BLIP caption & color display
# # ==========================
# def do_recommend(city: str, time_of_day: str, season: str, occasion: str, state: Dict):
#     weather = fetch_weather(city)
#     if not weather:
#         return (
#             "❌ Failed to fetch weather. Check the city name and API key.",
#             gr.update(), "Top: (unchanged)",
#             gr.update(), "Bottom: (unchanged)",
#             gr.update(), "Outerwear: (unchanged)",
#             state or {}
#         )

#     feats = {
#         "temperature": weather["temperature"],
#         "feels_like": weather["feels_like"],
#         "humidity": weather["humidity"],
#         "wind_speed": weather["wind_speed"],
#         "weather_condition": weather["weather_condition"],
#         "time_of_day": time_of_day,
#         "season": season,
#         "occasion": occasion,
#     }

#     pt, pb, po = predict_outfit(feats)
#     seed = random.randint(0, 10_000_000)
#     rng = random.Random(seed)

#     top = sanitize_prediction(pt, "top", rng)
#     bottom = sanitize_prediction(pb, "bottom", rng)
#     outer = sanitize_prediction(po, "outer", rng)

#     # Save predictions to state
#     state = {"preds": {"top": top, "bottom": bottom, "outer": outer}, "seed": seed}

#     # Pick representative images
#     images = {
#         "top": pick_image_for_label(top, rng),
#         "bottom": pick_image_for_label(bottom, rng),
#         "outer": pick_image_for_label(outer, rng),
#     }
#     state["images"] = images

#     # Generate captions and extract colors for these representative images
#     top_cap_raw = get_blip_caption_cached(images["top"]) if images["top"] else ""
#     bottom_cap_raw = get_blip_caption_cached(images["bottom"]) if images["bottom"] else ""
#     outer_cap_raw = get_blip_caption_cached(images["outer"]) if images["outer"] else ""

#     top_color = extract_color_from_caption(top_cap_raw) or "Unknown"
#     bottom_color = extract_color_from_caption(bottom_cap_raw) or "Unknown"
#     outer_color = extract_color_from_caption(outer_cap_raw) or "Unknown"

#     top_cap = f"👕 Top: {top}\n📝 {top_cap_raw or '(no caption)'}\n🎨 Detected color: {top_color.capitalize() if top_color!='Unknown' else 'Unknown'}"
#     bottom_cap = f"👖 Bottom: {bottom}\n📝 {bottom_cap_raw or '(no caption)'}\n🎨 Detected color: {bottom_color.capitalize() if bottom_color!='Unknown' else 'Unknown'}"
#     outer_cap = f"🧥 Outerwear: {outer if outer!='none' else 'None needed'}\n📝 {outer_cap_raw or '(no caption)'}\n🎨 Detected color: {outer_color.capitalize() if outer_color!='Unknown' else 'Unknown'}"

#     weather_text = (
#         f"🌤️ {weather['weather_condition'].capitalize()} | 🌡️ {weather['temperature']}°C "
#         f"(feels {weather['feels_like']}°C) | 💧 {weather['humidity']}% | 💨 {weather['wind_speed']} m/s"
#     )

#     return weather_text, images["top"], top_cap, images["bottom"], bottom_cap, images["outer"], outer_cap, state

# # ==========================
# # Mood Module (caption-based color filtering)
# # ==========================
# def filter_images_by_color_using_captions(color: str, label: str) -> List[str]:
#     """Scan all images in label folder, generate captions, extract colors from captions, and return matches."""
#     if not color or not label or label.lower() == "none":
#         return []
#     folder = IMAGES_ROOT / label.lower()
#     if not folder.exists():
#         return []

#     requested = normalize_and_canonicalize_color_input(color)
#     matches: List[str] = []

#     # Precompute captions for all images in label
#     precompute_captions_for_label(label)

#     for p in folder.iterdir():
#         if p.suffix.lower() not in VALID_EXTS:
#             continue
#         img_path = str(p)
#         cap = _caption_cache.get(img_path, "")  # lowercased caption
#         if not cap:
#             continue

#         # 1) Direct word match (alias-aware)
#         # example: requested 'blue' should match 'navy blue' and 'blue'
#         if re.search(rf"\b{re.escape(requested)}\b", cap):
#             matches.append(img_path)
#             continue

#         # 2) Check detected color from caption
#         det = extract_color_from_caption(cap)
#         if det and normalize_and_canonicalize_color_input(det) == requested:
#             matches.append(img_path)
#             continue

#         # 3) Substring fallback — match 'navy' when user typed 'blue' if caption contains both
#         # We include substring fallback to catch 'navy blue' vs 'blue' cases
#         if requested in cap:
#             matches.append(img_path)
#             continue

#     return matches

# def normalize_and_canonicalize_color_input(color: str) -> str:
#     c = (color or "").strip().lower()
#     if not c:
#         return c
#     c = normalize_color_word(c)
#     # canonical mapping: map synonyms to base color if needed
#     # map navy -> navy (we treat navy distinct), but user typing 'blue' should still match navy via substring fallback above
#     return c

# def filter_images_by_color_filename_fallback(color: str, label: str) -> List[str]:
#     """Fallback: search filenames for normalized color token."""
#     if not color or not label or label.lower() == "none":
#         return []
#     folder = IMAGES_ROOT / label.lower()
#     if not folder.exists():
#         return []
#     tok = normalize_and_canonicalize_color_input(color)
#     return [
#         str(p) for p in folder.iterdir()
#         if p.suffix.lower() in VALID_EXTS and tok in p.name.lower()
#     ]

# def do_color_filter(top_color, bottom_color, outer_color, state):
#     """Gradio handler: uses BLIP captions to find color matches across all images in predicted label folders."""
#     state = state or {}
#     preds = state.get("preds", {})
#     top_label = preds.get("top")
#     bottom_label = preds.get("bottom")
#     outer_label = preds.get("outer")

#     top_matches = []
#     bottom_matches = []
#     outer_matches = []

#     # Top
#     if top_color and top_label:
#         if BLIP_AVAILABLE:
#             top_matches = filter_images_by_color_using_captions(top_color, top_label)
#         else:
#             top_matches = filter_images_by_color_filename_fallback(top_color, top_label)

#     # Bottom
#     if bottom_color and bottom_label:
#         if BLIP_AVAILABLE:
#             bottom_matches = filter_images_by_color_using_captions(bottom_color, bottom_label)
#         else:
#             bottom_matches = filter_images_by_color_filename_fallback(bottom_color, bottom_label)

#     # Outer
#     if outer_color and outer_label and outer_label.lower() != "none":
#         if BLIP_AVAILABLE:
#             outer_matches = filter_images_by_color_using_captions(outer_color, outer_label)
#         else:
#             outer_matches = filter_images_by_color_filename_fallback(outer_color, outer_label)

#     # If no matches found, return friendly message
#     if not any([top_matches, bottom_matches, outer_matches]):
#         return (
#             "⚠️ No matches found. Try synonyms (e.g., 'grey'/'gray', 'navy', 'beige') or precompute captions for your dataset.",
#             [], "", [], "", [], "", state
#         )

#     top_caption = f"Top ({top_label}) — {top_color or 'N/A'} — {len(top_matches)} match(es)" if top_label else ""
#     bottom_caption = f"Bottom ({bottom_label}) — {bottom_color or 'N/A'} — {len(bottom_matches)} match(es)" if bottom_label else ""
#     outer_caption = f"Outerwear ({outer_label}) — {outer_color or 'N/A'} — {len(outer_matches)} match(es)" if outer_label else ""

#     return (
#         "🎨 Showing color-filtered matches (caption-based):",
#         top_matches, top_caption,
#         bottom_matches, bottom_caption,
#         outer_matches, outer_caption,
#         state
#     )

# # ==========================
# # Gradio UI
# # ==========================
# with gr.Blocks(title="AI Outfit Recommender (Weather + BLIP + Mood Module)") as demo:
#     gr.Markdown("## 👗 AI Clothing Recommender — Weather + BLIP Captions + Caption-based Mood Module")

#     with gr.Row():
#         city = gr.Textbox(label="City", value="Lahore")
#         time_of_day = gr.Dropdown(["morning", "afternoon", "evening", "night"], value="morning")
#         season = gr.Dropdown(["summer", "winter", "spring", "autumn"], value="summer")
#         occasion = gr.Dropdown(["casual", "formal", "party", "sports"], value="casual")

#     state = gr.State({})

#     recommend_btn = gr.Button("💡 Recommend Outfit", variant="primary")
#     weather_box = gr.Markdown()

#     with gr.Row():
#         top_img = gr.Image(label="Top", type="filepath")
#         top_cap = gr.Markdown()
#     with gr.Row():
#         bottom_img = gr.Image(label="Bottom", type="filepath")
#         bottom_cap = gr.Markdown()
#     with gr.Row():
#         outer_img = gr.Image(label="Outerwear", type="filepath")
#         outer_cap = gr.Markdown()

#     recommend_btn.click(
#         fn=do_recommend,
#         inputs=[city, time_of_day, season, occasion, state],
#         outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state],
#     )

#     # ---------------- Mood Module ----------------
#     gr.Markdown("---")
#     gr.Markdown("## 🎨 Mood Module — Filter by Your Favorite Colors (caption-based)")

#     with gr.Row():
#         top_color = gr.Textbox(label="Preferred color for Top (e.g., blue, green, navy)")
#         bottom_color = gr.Textbox(label="Preferred color for Bottom")
#         outer_color = gr.Textbox(label="Preferred color for Outerwear (optional)")

#     mood_btn = gr.Button("🎨 Show Outfits in My Colors", variant="secondary")
#     mood_info = gr.Markdown()

#     with gr.Row():
#         mood_top_gallery = gr.Gallery(label="Top Matches", columns=3, height="auto")
#         mood_top_cap = gr.Markdown()
#     with gr.Row():
#         mood_bottom_gallery = gr.Gallery(label="Bottom Matches", columns=3, height="auto")
#         mood_bottom_cap = gr.Markdown()
#     with gr.Row():
#         mood_outer_gallery = gr.Gallery(label="Outerwear Matches", columns=3, height="auto")
#         mood_outer_cap = gr.Markdown()

#     mood_btn.click(
#         fn=do_color_filter,
#         inputs=[top_color, bottom_color, outer_color, state],
#         outputs=[
#             mood_info,
#             mood_top_gallery, mood_top_cap,
#             mood_bottom_gallery, mood_bottom_cap,
#             mood_outer_gallery, mood_outer_cap,
#             state,
#         ]
#     )

#     # Optional: Button to precompute captions for predicted folders (faster subsequent queries)
#     def precompute_for_current(state):
#         st = state or {}
#         preds = st.get("preds", {})
#         labels = [preds.get("top"), preds.get("bottom"), preds.get("outer")]
#         # run precompute for each (non-none)
#         for lbl in labels:
#             if lbl and lbl.lower() != "none":
#                 precompute_captions_for_label(lbl)
#         return "✅ Captions precomputed for current predicted folders.", state

#     precompute_btn = gr.Button("🗂️ Precompute captions for current predicted folders")
#     precompute_res = gr.Markdown()
#     precompute_btn.click(fn=precompute_for_current, inputs=[state], outputs=[precompute_res, state])
# def precompute_captions_for_label(label: str, progress_callback: Optional[callable] = None):
#     """Generate & cache captions for all images in a given label folder."""
#     if not label or label.lower() == "none":
#         return
#     folder = IMAGES_ROOT / label.lower()
#     if not folder.exists():
#         return
#     files = [p for p in folder.iterdir() if p.suffix.lower() in VALID_EXTS]
#     for idx, f in enumerate(files):
#         _ = get_blip_caption_cached(f.as_posix())
#         if progress_callback:
#             progress_callback(f"{label}: {idx + 1}/{len(files)}")

# # ==========================
# # Weather-based outfit prediction
# # ==========================
# def do_recommend(city: str, time_of_day: str, season: str, occasion: str, state: Dict):
#     weather = fetch_weather(city)
#     if not weather:
#         return (
#             "❌ Failed to fetch weather.",
#             gr.update(), "Top: (unchanged)",
#             gr.update(), "Bottom: (unchanged)",
#             gr.update(), "Outerwear: (unchanged)",
#             state or {}
#         )

#     feats = {
#         "temperature": weather["temperature"],
#         "feels_like": weather["feels_like"],
#         "humidity": weather["humidity"],
#         "wind_speed": weather["wind_speed"],
#         "weather_condition": weather["weather_condition"],
#         "time_of_day": time_of_day,
#         "season": season,
#         "occasion": occasion,
#     }

#     pt, pb, po = predict_outfit(feats)
#     seed = random.randint(0, 10_000_000)
#     rng = random.Random(seed)

#     top = sanitize_prediction(pt, "top", rng)
#     bottom = sanitize_prediction(pb, "bottom", rng)
#     outer = sanitize_prediction(po, "outer", rng)

#     images = {
#         "top": pick_image_for_label(top, rng),
#         "bottom": pick_image_for_label(bottom, rng),
#         "outer": pick_image_for_label(outer, rng),
#     }

#     # generate captions
#     captions = {
#         slot: get_blip_caption_cached(path) if path else ""
#         for slot, path in images.items()
#     }

#     state = {
#         "preds": {"top": top, "bottom": bottom, "outer": outer},
#         "images": images,
#         "captions": captions,
#         "seed": seed,
#     }

#     weather_text = (
#         f"🌤️ {weather['weather_condition'].capitalize()} | 🌡️ {weather['temperature']}°C "
#         f"(feels {weather['feels_like']}°C) | 💧 {weather['humidity']}% | 💨 {weather['wind_speed']} m/s"
#     )

#     return (
#         weather_text,
#         images["top"], f"👕 Top: {top}\n📝 {captions['top'] or 'No caption'}",
#         images["bottom"], f"👖 Bottom: {bottom}\n📝 {captions['bottom'] or 'No caption'}",
#         images["outer"], f"🧥 Outerwear: {outer if outer != 'none' else 'None'}\n📝 {captions['outer'] or 'No caption'}",
#         state
#     )

# # ==========================
# # Mood filter (color-based search)
# # ==========================
# def filter_by_caption_color(color_pref: str, slot: str, state: Dict):
#     """Filter already predicted label images by matching caption color words."""
#     if not color_pref:
#         return []
#     color_pref = normalize_color_word(color_pref)
#     preds = state.get("preds", {})
#     label = preds.get(slot)
#     if not label or label.lower() == "none":
#         return []
#     folder = IMAGES_ROOT / label.lower()
#     if not folder.exists():
#         return []
#     files = [p for p in folder.iterdir() if p.suffix.lower() in VALID_EXTS]
#     matches = []
#     for f in files:
#         cap = get_blip_caption_cached(f.as_posix())
#         extracted_color = extract_color_from_caption(cap)
#         if extracted_color and extracted_color == color_pref:
#             matches.append(f.as_posix())
#     return matches

# def do_mood_filter(top_color, bottom_color, outer_color, state):
#     state = state or {}
#     results = {
#         "top": filter_by_caption_color(top_color, "top", state),
#         "bottom": filter_by_caption_color(bottom_color, "bottom", state),
#         "outer": filter_by_caption_color(outer_color, "outer", state),
#     }

#     if not any(results.values()):
#         return (
#             "⚠️ No color matches found in captions.",
#             [], "", [], "", [], "", state
#         )

#     return (
#         "🎨 Showing caption-based color matches:",
#         results["top"], f"Top matches for '{top_color or 'N/A'}'",
#         results["bottom"], f"Bottom matches for '{bottom_color or 'N/A'}'",
#         results["outer"], f"Outerwear matches for '{outer_color or 'N/A'}'",
#         state
#     )

# # ==========================
# # Reroll
# # ==========================
# def do_reroll(slot: str, state: Dict):
#     state = state or {}
#     preds = state.get("preds", {})
#     images = state.get("images", {})
#     seed = state.get("seed", random.randint(0, 10_000_000))
#     rng = random.Random(seed)

#     current = preds.get(slot)
#     allowed = allowed_labels_for(slot)
#     existing = [lbl for lbl in allowed if folder_has_images(lbl)]
#     options = [lbl for lbl in existing if lbl != current]
#     new_label = rng.choice(options) if options else current

#     preds[slot] = new_label
#     state["preds"] = preds

#     if slot == "outer" and new_label == "none":
#         images["outer"] = None
#     else:
#         images[slot] = pick_image_for_label(new_label, rng)
#     state["images"] = images

#     cap = get_blip_caption_cached(images[slot]) if images.get(slot) else ""
#     state.setdefault("captions", {})[slot] = cap

#     caption_text = f"{slot.capitalize()}: {new_label}\n📝 {cap or 'No caption'}"
#     if slot == "outer" and new_label == "none":
#         caption_text = "Outerwear: None needed"

#     empty = (gr.update(), gr.update())
#     if slot == "top":
#         return (gr.update(), images["top"], caption_text, *empty, *empty, state)
#     if slot == "bottom":
#         return (gr.update(), *empty, images["bottom"], caption_text, *empty, state)
#     return (gr.update(), *empty, *empty, images["outer"], caption_text, state)

# # ==========================
# # Gradio UI
# # ==========================
# with gr.Blocks(title="AI Outfit Recommender (Weather + Mood + BLIP)") as demo:
#     gr.Markdown("# 👗 WearSmart — AI Outfit Recommender")
#     gr.Markdown("**Powered by Weather, BLIP Captioning, and Color-based Mood Filtering**")

#     with gr.Row():
#         city = gr.Textbox(label="🌆 City")
#         time_of_day = gr.Dropdown(["morning", "afternoon", "evening", "night"], value="morning")
#         season = gr.Dropdown(["summer", "winter", "spring", "autumn"], value="summer")
#         occasion = gr.Dropdown(["casual", "formal", "party", "sports"], value="casual")

#     state = gr.State({})

#     recommend_btn = gr.Button("💡 Recommend Outfit", variant="primary")
#     weather_box = gr.Markdown()

#     with gr.Row():
#         top_img = gr.Image(label="Top", type="filepath")
#         top_cap = gr.Markdown()
#     with gr.Row():
#         bottom_img = gr.Image(label="Bottom", type="filepath")
#         bottom_cap = gr.Markdown()
#     with gr.Row():
#         outer_img = gr.Image(label="Outerwear", type="filepath")
#         outer_cap = gr.Markdown()

#     with gr.Row():
#         reroll_top = gr.Button("🔁 Reroll Top")
#         reroll_bottom = gr.Button("🔁 Reroll Bottom")
#         reroll_outer = gr.Button("🔁 Reroll Outerwear")

#     recommend_btn.click(
#         fn=do_recommend,
#         inputs=[city, time_of_day, season, occasion, state],
#         outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state],
#     )

#     reroll_top.click(lambda s: do_reroll("top", s),
#         inputs=[state],
#         outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state])
#     reroll_bottom.click(lambda s: do_reroll("bottom", s),
#         inputs=[state],
#         outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state])
#     reroll_outer.click(lambda s: do_reroll("outer", s),
#         inputs=[state],
#         outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state])

#     gr.Markdown("---")
#     gr.Markdown("## 🎨 Mood Filter — Based on Captioned Colors")

#     with gr.Row():
#         top_color = gr.Textbox(label="Preferred color for Top")
#         bottom_color = gr.Textbox(label="Preferred color for Bottom")
#         outer_color = gr.Textbox(label="Preferred color for Outerwear")

#     mood_btn = gr.Button("🎨 Filter by My Colors", variant="secondary")
#     mood_info = gr.Markdown()

#     with gr.Row():
#         mood_top_gallery = gr.Gallery(label="Top Matches", columns=3, height="auto")
#         mood_top_cap = gr.Markdown()
#     with gr.Row():
#         mood_bottom_gallery = gr.Gallery(label="Bottom Matches", columns=3, height="auto")
#         mood_bottom_cap = gr.Markdown()
#     with gr.Row():
#         mood_outer_gallery = gr.Gallery(label="Outerwear Matches", columns=3, height="auto")
#         mood_outer_cap = gr.Markdown()

#     mood_btn.click(
#         fn=do_mood_filter,
#         inputs=[top_color, bottom_color, outer_color, state],
#         outputs=[
#             mood_info,
#             mood_top_gallery, mood_top_cap,
#             mood_bottom_gallery, mood_bottom_cap,
#             mood_outer_gallery, mood_outer_cap,
#             state,
#         ]
#     )

# if __name__ == "__main__":
#     demo.launch()


# app_gradio.py
# AI Outfit Recommender with Weather + BLIP Captioning + Color Detection + Mood Module + Manual Selection
import os
import random
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import gradio as gr
import pandas as pd
import joblib
import requests
from PIL import Image
import re

from dynamic_shopping_recommender import generate_dynamic_shopping_recommendations
import csv
from datetime import datetime

# ==========================
# BLIP Captioning Setup
# ==========================
BLIP_AVAILABLE = True
try:
    import torch
    from transformers import BlipProcessor, BlipForConditionalGeneration
except Exception:
    BLIP_AVAILABLE = False
    BlipProcessor = BlipForConditionalGeneration = None

_blip_loaded = False
_blip_processor = None
_blip_model = None

def _load_blip():
    """Load fine-tuned or default BLIP model once (safe if unavailable)."""
    global _blip_loaded, _blip_processor, _blip_model
    if _blip_loaded or not BLIP_AVAILABLE:
        return
    try:
        local_dir = Path("blip_finetunedggdata")
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

def generate_caption(image_path: Optional[str]) -> str:
    """Generate caption for an image using BLIP. Returns empty string on failure."""
    if not image_path or not BLIP_AVAILABLE:
        return ""
    if not _blip_loaded:
        _load_blip()
    if not _blip_model or not _blip_processor:
        return ""
    try:
        img = Image.open(image_path).convert("RGB")
        inputs = _blip_processor(img, return_tensors="pt").to(_blip_model.device)
        out = _blip_model.generate(**inputs, max_new_tokens=24)
        caption = _blip_processor.decode(out[0], skip_special_tokens=True)
        return caption
    except Exception as e:
        print(f"[BLIP caption error] {e}")
        return ""

# ==========================
# Color extraction + aliases
# ==========================
COLOR_NAMES = [
    "red", "green", "blue", "yellow", "orange", "purple", "pink",
    "brown", "black", "white", "gray", "beige", "maroon", "navy",
    "teal", "cyan", "gold", "silver", "cream"
]

COLOR_ALIASES = {
    "grey": "gray", "charcoal": "gray", "slate": "gray", "ash": "gray",
    "smoke": "gray", "graphite": "gray", "gunmetal": "gray", "pewter": "gray",
    "sky": "blue", "navy": "blue", "teal": "blue", "turquoise": "blue",
    "aqua": "blue", "azure": "blue", "babyblue": "blue", "cobalt": "blue",
    "indigo": "blue", "royalblue": "blue", "denim": "blue", "sapphire": "blue",
    "midnight": "blue", "crimson": "red", "scarlet": "red", "ruby": "red",
    "cherry": "red", "garnet": "red", "blood": "red", "rosewood": "red",
    "rust": "red", "wine": "red", "brick": "red", "mahogany": "red",
    "burgundy": "maroon", "oxblood": "maroon", "berry": "maroon",
    "plum": "maroon", "raisin": "maroon", "lime": "green", "olive": "green",
    "forest": "green", "emerald": "green", "mint": "green", "sage": "green",
    "moss": "green", "seafoam": "green", "jade": "green", "chartreuse": "green",
    "avocado": "green", "basil": "green", "golden": "gold", "mustard": "yellow",
    "lemon": "yellow", "amber": "yellow", "honey": "yellow", "canary": "yellow",
    "sunflower": "yellow", "beige": "yellow", "sand": "yellow", "camel": "yellow",
    "khaki": "yellow", "tan": "yellow", "apricot": "orange", "peach": "orange",
    "tangerine": "orange", "coral": "orange", "salmon": "orange",
    "terracotta": "orange", "rusty": "orange", "pumpkin": "orange",
    "violet": "purple", "lavender": "purple", "lilac": "purple", "mauve": "purple",
    "orchid": "purple", "amethyst": "purple", "magenta": "purple",
    "eggplant": "purple", "rose": "pink", "blush": "pink", "fuchsia": "pink",
    "hotpink": "pink", "salmonpink": "pink", "baby pink": "pink",
    "bubblegum": "pink", "coralpink": "pink", "peony": "pink", "dustyrose": "pink",
    "chocolate": "brown", "coffee": "brown", "mocha": "brown", "walnut": "brown",
    "caramel": "brown", "bronze": "brown", "copper": "brown", "espresso": "brown",
    "rustbrown": "brown", "hazel": "brown", "offwhite": "white", "off-white": "white",
    "ivory": "white", "cream": "white", "eggshell": "white", "snow": "white",
    "pearl": "white", "linen": "white", "porcelain": "white", "jet": "black",
    "onyx": "black", "ebony": "black", "coal": "black", "ink": "black",
    "char": "black", "graphiteblack": "black", "platinum": "silver",
    "chrome": "silver", "metallic": "silver", "steel": "silver",
}

def normalize_color_word(word: str) -> str:
    w = (word or "").strip().lower()
    return COLOR_ALIASES.get(w, w)

def extract_color_from_caption(caption: str) -> Optional[str]:
    """Return first matched color name (canonicalized) or None."""
    if not caption:
        return None
    text = caption.lower()
    for c in COLOR_NAMES:
        if re.search(rf"\b{re.escape(c)}\b", text):
            return c
    for alias, canonical in COLOR_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return canonical
    return None

# ==========================
# Config
# ==========================
MODEL_PATH = Path("weather_clothing_recommender_women.pkl")
IMAGES_ROOT = Path("clothing_images")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "4c703f15e3f9220de836884137342d5d")
REQUEST_TIMEOUT = 10

# Updated clothing categories based on your folder structure
TOP_LABELS = ["tops", "shirts", "kurtas"]
BOTTOM_LABELS = ["trousers", "jeans", "leggings", "capris"]
OUTER_LABELS = ["none", "coat", "jacket", "puffer_jacket", "dupatta"]

def get_available_items(category: str) -> List[str]:
    """Get available items for a category based on existing folders."""
    if category == "top":
        return [item for item in TOP_LABELS if folder_has_images(item)]
    elif category == "bottom":
        return [item for item in BOTTOM_LABELS if folder_has_images(item)]
    elif category == "outer":
        return [item for item in OUTER_LABELS if item == "none" or folder_has_images(item)]
    return []

def allowed_labels_for(slot: str) -> set:
    if slot == "top":
        return {x.lower() for x in TOP_LABELS}
    if slot == "bottom":
        return {x.lower() for x in BOTTOM_LABELS}
    return {x.lower() for x in OUTER_LABELS}

# ==========================
# Weather fetch
# ==========================
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

# ==========================
# Model load
# ==========================
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH.resolve()}")
_model = joblib.load(MODEL_PATH.as_posix())

def predict_outfit(features: Dict) -> Tuple[str, str, str]:
    df = pd.DataFrame([features])
    return _model.predict(df)[0]

# ==========================
# Image utils
# ==========================
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

def folder_has_images(label: str) -> bool:
    if (label or "").lower() == "none":
        return True
    p = IMAGES_ROOT / (label or "").lower()
    return p.is_dir() and any(f.suffix.lower() in VALID_EXTS for f in p.iterdir())

def pick_image_for_label(label: str, rng: random.Random) -> Optional[str]:
    if label is None or label.lower() == "none":
        return None
    folder = IMAGES_ROOT / label.lower()
    if not folder.is_dir():
        return None
    files = [p for p in folder.iterdir() if p.suffix.lower() in VALID_EXTS]
    return rng.choice(files).as_posix() if files else None

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
    # Try to find a different image
    options = [f for f in files if f != (current_path or "")]
    return rng.choice(options) if options else current_path

def sanitize_prediction(label: str, slot: str, rng: random.Random) -> str:
    allowed = allowed_labels_for(slot)
    lbl = (label or "").lower()
    if lbl in allowed and folder_has_images(lbl):
        return lbl
    candidates = [x for x in allowed if folder_has_images(x)]
    return rng.choice(candidates) if candidates else lbl or ""

# ==========================
# Caption cache (in-memory)
# ==========================
_caption_cache: Dict[str, str] = {}

def get_blip_caption_cached(image_path: str) -> str:
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

# ==========================
# Weather-based recommendation
# ==========================
def do_recommend(city: str, time_of_day: str, season: str, occasion: str, state: Dict):
    weather = fetch_weather(city)
    if not weather:
        return (
            "❌ Failed to fetch weather. Check the city name and API key.",
            gr.update(), "Top: (unchanged)",
            gr.update(), "Bottom: (unchanged)",
            gr.update(), "Outerwear: (unchanged)",
            gr.update(choices=[]), gr.update(choices=[]), gr.update(choices=[]),
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

    pt, pb, po = predict_outfit(feats)
    seed = random.randint(0, 10_000_000)
    rng = random.Random(seed)

    top = sanitize_prediction(pt, "top", rng)
    bottom = sanitize_prediction(pb, "bottom", rng)
    outer = sanitize_prediction(po, "outer", rng)

    state = {"preds": {"top": top, "bottom": bottom, "outer": outer}, "seed": seed}

    images = {
        "top": pick_image_for_label(top, rng),
        "bottom": pick_image_for_label(bottom, rng),
        "outer": pick_image_for_label(outer, rng),
    }
    state["images"] = images

    top_cap_raw = get_blip_caption_cached(images["top"]) if images["top"] else ""
    bottom_cap_raw = get_blip_caption_cached(images["bottom"]) if images["bottom"] else ""
    outer_cap_raw = get_blip_caption_cached(images["outer"]) if images["outer"] else ""

    top_color = extract_color_from_caption(top_cap_raw) or "Unknown"
    bottom_color = extract_color_from_caption(bottom_cap_raw) or "Unknown"
    outer_color = extract_color_from_caption(outer_cap_raw) or "Unknown"

    top_cap = f"👕 Top: {top}\n📝 {top_cap_raw or '(no caption)'}\n🎨 Detected color: {top_color.capitalize() if top_color!='Unknown' else 'Unknown'}"
    bottom_cap = f"👖 Bottom: {bottom}\n📝 {bottom_cap_raw or '(no caption)'}\n🎨 Detected color: {bottom_color.capitalize() if bottom_color!='Unknown' else 'Unknown'}"
    outer_cap = f"🧥 Outerwear: {outer if outer!='none' else 'None needed'}\n📝 {outer_cap_raw or '(no caption)'}\n🎨 Detected color: {outer_color.capitalize() if outer_color!='Unknown' else 'Unknown'}"

    weather_text = (
        f"🌤️ {weather['weather_condition'].capitalize()} | 🌡️ {weather['temperature']}°C "
        f"(feels {weather['feels_like']}°C) | 💧 {weather['humidity']}% | 💨 {weather['wind_speed']} m/s"
    )

    # Get available items for dropdowns
    top_choices = get_available_items("top")
    bottom_choices = get_available_items("bottom")
    outer_choices = get_available_items("outer")

    return (
        weather_text,
        images["top"], top_cap,
        images["bottom"], bottom_cap,
        images["outer"], outer_cap,
        gr.update(choices=top_choices, value=top),
        gr.update(choices=bottom_choices, value=bottom),
        gr.update(choices=outer_choices, value=outer),
        state
    )

# ==========================
# Manual item change (dropdown)
# ==========================
def change_item(selected_item: str, slot: str, state: Dict):
    """Change the displayed item when user selects from dropdown."""
    state = state or {}
    preds = state.get("preds", {})
    images = state.get("images", {})
    seed = state.get("seed", random.randint(0, 10_000_000))
    rng = random.Random(seed)

    # Update prediction
    preds[slot] = selected_item
    state["preds"] = preds

    # Get new image
    if slot == "outer" and selected_item == "none":
        images[slot] = None
    else:
        images[slot] = pick_image_for_label(selected_item, rng)
    state["images"] = images

    # Generate caption
    cap = get_blip_caption_cached(images[slot]) if images.get(slot) else ""
    color = extract_color_from_caption(cap) or "Unknown"
    
    caption_text = f"{slot.capitalize()}: {selected_item}\n📝 {cap or '(no caption)'}\n🎨 Detected color: {color.capitalize() if color!='Unknown' else 'Unknown'}"
    if slot == "outer" and selected_item == "none":
        caption_text = "🧥 Outerwear: None needed"

    # Return updates based on slot
    empty_img = gr.update()
    empty_cap = gr.update()
    
    if slot == "top":
        return images["top"], caption_text, empty_img, empty_cap, empty_img, empty_cap, state
    elif slot == "bottom":
        return empty_img, empty_cap, images["bottom"], caption_text, empty_img, empty_cap, state
    else:  # outer
        return empty_img, empty_cap, empty_img, empty_cap, images["outer"], caption_text, state

# ==========================
# Reroll (keeps label fixed, shuffle images)
# ==========================
def do_reroll(slot: str, state: Dict):
    """Shuffle a new image within the SAME label for the chosen slot."""
    state = state or {}
    preds = state.get("preds") or {}
    images = state.get("images") or {}

    if slot not in {"top", "bottom", "outer"} or not preds.get(slot):
        return (
            gr.update(),
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            state
        )

    seed = state.get("seed", random.randint(0, 10_000_000))
    rng = random.Random(seed + random.randint(1, 1000))  # Add randomness for different image
    state["seed"] = seed + 1

    label = preds[slot]  # KEEP label fixed
    new_img = pick_new_image_same_label(label, images.get(slot), rng)
    images[slot] = new_img
    state["images"] = images

    # Generate caption for new image
    cap = get_blip_caption_cached(new_img) if new_img else ""
    color = extract_color_from_caption(cap) or "Unknown"

    # Update only the changed slot
    if slot == "top":
        caption_text = f"👕 Top: {label}\n📝 {cap or '(no caption)'}\n🎨 Detected color: {color.capitalize() if color!='Unknown' else 'Unknown'}"
        return (
            gr.update(),
            images["top"], caption_text,
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            state
        )
    elif slot == "bottom":
        caption_text = f"👖 Bottom: {label}\n📝 {cap or '(no caption)'}\n🎨 Detected color: {color.capitalize() if color!='Unknown' else 'Unknown'}"
        return (
            gr.update(),
            gr.update(), gr.update(),
            images["bottom"], caption_text,
            gr.update(), gr.update(),
            state
        )
    else:  # outer
        if label == "none":
            caption_text = "🧥 Outerwear: None needed"
            return (
                gr.update(),
                gr.update(), gr.update(),
                gr.update(), gr.update(),
                None, caption_text,
                state
            )
        else:
            caption_text = f"🧥 Outerwear: {label}\n📝 {cap or '(no caption)'}\n🎨 Detected color: {color.capitalize() if color!='Unknown' else 'Unknown'}"
            return (
                gr.update(),
                gr.update(), gr.update(),
                gr.update(), gr.update(),
                images["outer"], caption_text,
                state
            )

# ==========================
# Mood Module (caption-based color filtering)
# ==========================
def filter_images_by_color_using_captions(color: str, label: str) -> List[str]:
    """Scan all images in label folder, generate captions, extract colors from captions, and return matches."""
    if not color or not label or label.lower() == "none":
        return []
    folder = IMAGES_ROOT / label.lower()
    if not folder.exists():
        return []

    requested = normalize_color_word(color.lower())
    matches: List[str] = []

    precompute_captions_for_label(label)

    for p in folder.iterdir():
        if p.suffix.lower() not in VALID_EXTS:
            continue
        img_path = str(p)
        cap = _caption_cache.get(img_path, "")
        if not cap:
            continue

        if re.search(rf"\b{re.escape(requested)}\b", cap):
            matches.append(img_path)
            continue

        det = extract_color_from_caption(cap)
        if det and normalize_color_word(det) == requested:
            matches.append(img_path)
            continue

        if requested in cap:
            matches.append(img_path)
            continue

    return matches

def do_color_filter(top_color, bottom_color, outer_color, state):
    """Gradio handler: uses BLIP captions to find color matches."""
    state = state or {}
    preds = state.get("preds", {})
    top_label = preds.get("top")
    bottom_label = preds.get("bottom")
    outer_label = preds.get("outer")

    top_matches = []
    bottom_matches = []
    outer_matches = []

    if top_color and top_label:
        if BLIP_AVAILABLE:
            top_matches = filter_images_by_color_using_captions(top_color, top_label)

    if bottom_color and bottom_label:
        if BLIP_AVAILABLE:
            bottom_matches = filter_images_by_color_using_captions(bottom_color, bottom_label)

    if outer_color and outer_label and outer_label.lower() != "none":
        if BLIP_AVAILABLE:
            outer_matches = filter_images_by_color_using_captions(outer_color, outer_label)

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

def show_shopping_recommendations(state):
    """Show shopping recommendations based on current wardrobe."""
    state = state or {}
    season = state.get("season", "summer")
    caption_cache = state.get("captions", {})
    
    # Generate dynamic recommendations using real web data
    wardrobe_summary, gap_analysis, shopping_list, product_images, product_links = generate_dynamic_shopping_recommendations(
        images_root=str(IMAGES_ROOT),
        season=season,
        caption_cache=caption_cache,
        gender="women"
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
        "gender": "female",
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

# ==========================
# Gradio UI
# ==========================
with gr.Blocks(title="AI Outfit Recommender (Weather + BLIP + Mood Module)") as demo:
    gr.Markdown("# 👗 WearSmart — AI Outfit Recommender")
    gr.Markdown("**Powered by Weather, BLIP Captioning, Manual Selection, and Reroll**")

    with gr.Row():
        city = gr.Textbox(label="🌆 City", value="Lahore")
        time_of_day = gr.Dropdown(["morning", "afternoon", "evening", "night"], value="morning", label="⏰ Time")
        season = gr.Dropdown(["summer", "winter", "spring", "autumn"], value="summer", label="🌸 Season")
        occasion = gr.Dropdown(["casual", "formal", "party", "sports"], value="casual", label="🎭 Occasion")

    state = gr.State({})

    recommend_btn = gr.Button("💡 Recommend Outfit", variant="primary")
    weather_box = gr.Markdown()

    with gr.Row():
        with gr.Column():
            top_img = gr.Image(label="Top", type="filepath")
            top_cap = gr.Markdown()
            top_dropdown = gr.Dropdown(label="Change Category", choices=[])
            reroll_top = gr.Button("🔁 Reroll Top Image", size="sm")
        
        with gr.Column():
            bottom_img = gr.Image(label="Bottom", type="filepath")
            bottom_cap = gr.Markdown()
            bottom_dropdown = gr.Dropdown(label="Change Category", choices=[])
            reroll_bottom = gr.Button("🔁 Reroll Bottom Image", size="sm")
        
        with gr.Column():
            outer_img = gr.Image(label="Outerwear", type="filepath")
            outer_cap = gr.Markdown()
            outer_dropdown = gr.Dropdown(label="Change Category", choices=[])
            reroll_outer = gr.Button("🔁 Reroll Outerwear Image", size="sm")

    recommend_btn.click(
        fn=do_recommend,
        inputs=[city, time_of_day, season, occasion, state],
        outputs=[
            weather_box,
            top_img, top_cap,
            bottom_img, bottom_cap,
            outer_img, outer_cap,
            top_dropdown, bottom_dropdown, outer_dropdown,
            state
        ],
    )

    # Dropdown change handlers
    top_dropdown.change(
        fn=lambda item, s: change_item(item, "top", s),
        inputs=[top_dropdown, state],
        outputs=[top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state]
    )

    bottom_dropdown.change(
        fn=lambda item, s: change_item(item, "bottom", s),
        inputs=[bottom_dropdown, state],
        outputs=[top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state]
    )

    outer_dropdown.change(
        fn=lambda item, s: change_item(item, "outer", s),
        inputs=[outer_dropdown, state],
        outputs=[top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state]
    )

    # Reroll button handlers
    reroll_top.click(
        lambda s: do_reroll("top", s),
        inputs=[state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state]
    )

    reroll_bottom.click(
        lambda s: do_reroll("bottom", s),
        inputs=[state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state]
    )

    reroll_outer.click(
        lambda s: do_reroll("outer", s),
        inputs=[state],
        outputs=[weather_box, top_img, top_cap, bottom_img, bottom_cap, outer_img, outer_cap, state]
    )

    # Mood Module
    gr.Markdown("---")
    gr.Markdown("## 🎨 Mood Module — Filter by Your Favorite Colors")

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
    
    # Shopping Recommendations
    gr.Markdown("---")
    gr.Markdown("## 🛍️ Future Shopping Recommendations")
    
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
        fn=show_shopping_recommendations,
        inputs=[state],
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