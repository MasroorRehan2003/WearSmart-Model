# 🛍️ Shopping Recommender System

## 📋 Overview

This system analyzes your wardrobe and provides intelligent shopping recommendations based on:
- **BLIP Image Captions** - AI-powered color detection from images
- **Wardrobe Gaps** - Missing colors, categories, and seasonal needs
- **Smart Prioritization** - HIGH/MEDIUM/LOW priority recommendations

---

## 🚀 Quick Start

### Step 1: Generate BLIP Captions (One-Time Setup)

Run this **once** to generate captions for all your images:

```bash
python generate_captions.py
```

This will:
- ✅ Scan all images in `clothing_images_men/` and `clothing_images/`
- ✅ Generate AI captions using your BLIP model
- ✅ Save captions to JSON files:
  - `blip_captions_male.json`
  - `blip_captions_female.json`

**Time:** ~5-10 minutes depending on number of images

---

### Step 2: Use Shopping Recommender

The shopping recommender will **automatically** load the caption files when you click the button in your Gradio app.

**No additional setup needed!** 🎉

---

## 📁 File Structure

```
weather_module/
├── blip_caption_generator.py      # BLIP caption generation
├── generate_captions.py            # Quick script to generate captions
├── shopping_recommender_backend.py # Shopping recommendation logic
├── blip_captions_male.json         # Generated captions (male)
├── blip_captions_female.json       # Generated captions (female)
└── SHOPPING_RECOMMENDER_README.md  # This file
```

---

## 🎯 How It Works

### 1. **Caption Generation** (`blip_caption_generator.py`)
- Scans all images in your clothing folders
- Uses BLIP model to generate descriptive captions
- Stores captions in JSON format for fast access

### 2. **Color Detection**
- Extracts colors from BLIP captions (e.g., "blue shirt" → blue)
- Supports 20+ colors and aliases (navy→blue, grey→gray, etc.)
- Creates color distribution map of your wardrobe

### 3. **Gap Analysis** (`shopping_recommender_backend.py`)
- **Missing Colors**: Identifies colors you don't have
- **Underrepresented Categories**: Finds categories with few items
- **Seasonal Gaps**: Detects winter/summer clothing needs
- **Quantity Gaps**: Ensures minimum items per category

### 4. **Smart Recommendations**
Generates prioritized shopping list:
- 🔴 **HIGH**: Essential missing items (coats in winter, etc.)
- 🟡 **MEDIUM**: Color variety, category balance
- 🟢 **LOW**: Style variety, statement pieces

---

## 🎨 Example Output

```
📊 Current Wardrobe Analysis

Tops: 36 items
  - kurtas: 14 items (blue, red, green, white, purple)
  - shirts: 15 items (white, blue, black, gray, navy)
  - tops: 7 items (pink, purple, yellow)

Bottoms: 24 items
  - trousers: 15 items (black, beige, navy, gray)
  - jeans: 3 items (blue)
  - leggings: 3 items (black, gray)

Color Distribution:
  - Blue: 8 items
  - Black: 7 items
  - White: 5 items
  - Red: 4 items
  - Green: 3 items

🔍 Wardrobe Gap Analysis

Missing Colors: orange, yellow, pink, purple
Underrepresented Categories: outerwear
Seasonal Needs: warm_outerwear

🛍️ Shopping Recommendations

🔴 HIGH PRIORITY
1. Winter Coat or Jacket
   - Reason: Essential for winter season
   - Suggested Color: Any neutral color (black, gray, navy)

2. 2-3 Tops in orange, yellow
   - Reason: Add color variety to wardrobe
   - Suggested Color: orange, yellow

🟡 MEDIUM PRIORITY
3. Tops in orange, yellow, pink
   - Reason: Add color variety to wardrobe
   - Suggested Color: orange, yellow, pink

🟢 LOW PRIORITY
4. Statement piece (bright color or pattern)
   - Reason: Add personality to wardrobe
   - Suggested Color: Bright colors (yellow, pink, orange)
```

---

## 🔧 Integration with Gradio Apps

### For `mood_check_male.py`:

```python
# Add at top of file
from shopping_recommender_backend import generate_shopping_recommendations

# Add function before Gradio UI
def show_shopping_recommendations(state):
    state = state or {}
    season = state.get("season", "summer")
    
    wardrobe_summary, gap_analysis, shopping_list = generate_shopping_recommendations(
        images_root="clothing_images_men",
        season=season,
        caption_cache_path="blip_captions_male.json"
    )
    
    return wardrobe_summary, gap_analysis, shopping_list

# Add to Gradio UI (before if __name__ == "__main__")
gr.Markdown("---")
gr.Markdown("## 🛍️ Future Shopping Recommendations")

shopping_btn = gr.Button("🛍️ Analyze My Wardrobe & Get Shopping List", variant="primary", size="lg")

with gr.Row():
    with gr.Column():
        wardrobe_summary = gr.Markdown(label="Current Wardrobe")
    with gr.Column():
        gap_analysis = gr.Markdown(label="Gap Analysis")

shopping_list = gr.Markdown(label="Shopping Recommendations")

shopping_btn.click(
    fn=show_shopping_recommendations,
    inputs=[state],
    outputs=[wardrobe_summary, gap_analysis, shopping_list]
)
```

### For `mood_check_female.py`:

Same code, but change:
```python
images_root="clothing_images"  # instead of clothing_images_men
caption_cache_path="blip_captions_female.json"  # instead of male
```

---

## 🎨 Supported Colors

The system recognizes these colors (and their aliases):

### Basic Colors
- Red, Green, Blue, Yellow, Orange, Purple, Pink
- Brown, Black, White, Gray, Beige

### Extended Colors
- Maroon, Navy, Teal, Cyan, Gold, Silver, Cream

### Color Aliases
- **Blue**: sky, navy, teal, turquoise, aqua, azure, cobalt, indigo, royal blue, denim, sapphire, midnight
- **Red**: crimson, scarlet, ruby, cherry, garnet, wine, brick, mahogany
- **Green**: lime, olive, forest, emerald, mint, sage, moss, jade
- **Gray**: grey, charcoal, slate, ash, smoke, graphite, gunmetal, pewter
- **Yellow**: golden, mustard, lemon, amber, honey, canary, sunflower, sand, camel, khaki, tan
- **Orange**: apricot, peach, tangerine, coral, salmon, terracotta, pumpkin
- **Purple**: violet, lavender, lilac, mauve, orchid, amethyst, magenta, eggplant
- **Pink**: rose, blush, fuchsia, hot pink, bubblegum, peony, dusty rose
- **Brown**: chocolate, coffee, mocha, walnut, caramel, bronze, copper, espresso
- **White**: off-white, ivory, cream, eggshell, snow, pearl, linen, porcelain
- **Black**: jet, onyx, ebony, coal, ink, char

---

## 🔄 Updating Captions

If you add new images to your wardrobe:

```bash
python generate_captions.py
```

This will regenerate all captions (including new images).

---

## 💡 Tips

1. **First Time**: Run `generate_captions.py` before using shopping recommender
2. **GPU**: Caption generation is faster on GPU (CUDA)
3. **Season**: Update season parameter for seasonal recommendations
4. **Colors**: BLIP captions provide better color detection than filenames

---

## 🐛 Troubleshooting

### "Caption cache not found"
- Run `python generate_captions.py` first

### "BLIP model not found"
- Ensure `blip_finetunedggdata/` folder exists in project root

### "No colors detected"
- Check that BLIP captions were generated successfully
- Verify caption files exist (`blip_captions_male.json`, etc.)

---

## 📊 Performance

- **Caption Generation**: ~2-3 seconds per image (GPU), ~5-10 seconds (CPU)
- **Shopping Analysis**: < 1 second (uses cached captions)
- **Total Images**: ~100-200 images = 5-10 minutes (one-time setup)

---

## 🎉 That's It!

You now have an intelligent shopping recommender that:
- ✅ Analyzes your actual wardrobe
- ✅ Detects colors from AI captions
- ✅ Identifies gaps and missing items
- ✅ Provides prioritized shopping recommendations

Enjoy your smart wardrobe assistant! 🛍️✨

