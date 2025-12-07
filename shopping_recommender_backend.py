"""
🛍️ Shopping Recommender Backend
Standalone module for wardrobe gap analysis and shopping recommendations
Works with both male and female modules
"""

import os
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import Counter
import re

# ==========================
# Configuration
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

VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


# ==========================
# Helper Functions
# ==========================
def normalize_color_word(word: str) -> str:
    """Normalize color name to canonical form."""
    w = (word or "").strip().lower()
    return COLOR_ALIASES.get(w, w)


def extract_color_from_caption(caption: str) -> Optional[str]:
    """Extract color from BLIP caption."""
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


def _normalize_path_key(p: str) -> str:
    """Normalize file path for consistent dict keys (absolute, posix, lowercase)."""
    try:
        return Path(p).resolve().as_posix().lower()
    except Exception:
        # Fallback: best-effort normalization
        return str(p).replace("\\", "/").lower()


def _normalize_caption_cache_keys(cache: Dict[str, str]) -> Dict[str, str]:
    """Return a new dict with normalized absolute keys and anchor-tail variants."""
    if not cache:
        return {}
    out: Dict[str, str] = {}
    for k, v in cache.items():
        norm_key = _normalize_path_key(k)
        val = (v or "").strip()
        out[norm_key] = val
        for anchor in ("/clothing_images_men/", "/clothing_images/"):
            idx = norm_key.find(anchor)
            if idx != -1:
                tail = norm_key[idx+1:]
                out[tail] = val
    return out


def load_blip_caption_cache(cache_path: str = "blip_captions_cache.json") -> Dict[str, str]:
    """Load BLIP caption cache from JSON file and normalize keys to absolute posix lowercase."""
    import json
    from pathlib import Path
    
    cache_file = Path(cache_path)
    if not cache_file.exists():
        print(f"⚠️ Caption cache not found: {cache_path}")
        return {}
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        # Normalize keys; store absolute and tail-from images root variants
        captions = _normalize_caption_cache_keys(raw)
        print(f"✅ Loaded {len(captions)} captions from {cache_path}")
        return captions
    except Exception as e:
        print(f"❌ Error loading caption cache: {e}")
        return {}


# ==========================
# Wardrobe Analyzer
# ==========================
class WardrobeAnalyzer:
    """Analyze user's current wardrobe from image folders."""
    
    def __init__(self, images_root: Path, caption_cache: Dict[str, str] = None):
        self.images_root = Path(images_root)
        self.caption_cache = caption_cache or {}
        
        # Define item categories based on folder names
        self.top_items = {
            "shirt", "shirts", "t-shirt", "t-shirt", "kurta", "kurtas", 
            "sweater", "sweaters", "formal_shirts", "formal_shirt", "tops"
        }
        self.bottom_items = {
            "pants", "jeans", "shorts", "trousers", "cotton pants", "formal_pants",
            "formal_pant", "leggings", "capris"
        }
        self.outerwear_items = {
            "jacket", "jackets", "coat", "hoodie", "hoodies", "puffer_jacket",
            "dupatta", "outerwear", "none"
        }
        
    def _categorize_item(self, folder_name: str) -> str:
        """Categorize item folder into tops/bottoms/outerwear."""
        folder_lower = folder_name.lower()
        
        if folder_lower in self.top_items:
            return "tops"
        elif folder_lower in self.bottom_items:
            return "bottoms"
        elif folder_lower in self.outerwear_items:
            return "outerwear"
        else:
            # Default to tops if unknown
            return "tops"
        
    def scan_wardrobe(self) -> Dict:
        """Scan all clothing folders and extract wardrobe data."""
        wardrobe = {
            "tops": {},
            "bottoms": {},
            "outerwear": {},
            "total_items": 0,
            "color_distribution": Counter()
        }
        
        if not self.images_root.exists():
            return wardrobe
        
        # Scan all folders directly in the images root
        for item_folder in self.images_root.iterdir():
            if not item_folder.is_dir():
                continue
            
            # Skip special folders
            if item_folder.name.lower() in ["data", "none"]:
                continue
                
            item_name = item_folder.name
            colors = []
            item_count = 0
            
            # Scan images in this item folder
            for img_file in item_folder.iterdir():
                if img_file.suffix.lower() not in VALID_EXTS:
                    continue
                
                item_count += 1
                wardrobe["total_items"] += 1
                
                # Extract color from BLIP caption with robust key matching
                raw_path = str(img_file)
                img_key = _normalize_path_key(raw_path)
                caption = None
                # 1) absolute-normalized match
                if img_key in self.caption_cache:
                    caption = self.caption_cache[img_key]
                else:
                    # 2) relative tail match from known anchors
                    rel_posix = raw_path.replace("\\", "/").lower()
                    for anchor in ("clothing_images_men/", "clothing_images/"):
                        if anchor in rel_posix:
                            tail = rel_posix[rel_posix.index(anchor):]
                            if tail in self.caption_cache:
                                caption = self.caption_cache[tail]
                                break
                color = extract_color_from_caption(caption) if caption else None
                if color:
                    colors.append(color)
                    wardrobe["color_distribution"][color] += 1
            
            if item_count > 0:
                # Categorize this item
                category = self._categorize_item(item_name)
                wardrobe[category][item_name] = {
                    "count": item_count,
                    "colors": colors,
                    "unique_colors": list(set(colors))
                }
        
        return wardrobe


# ==========================
# Gap Analyzer
# ==========================
class GapAnalyzer:
    """Analyze gaps in wardrobe and generate recommendations."""
    
    def __init__(self, wardrobe_data: Dict, season: str = "summer"):
        self.wardrobe = wardrobe_data
        self.season = season.lower()
        
    def analyze_gaps(self) -> Dict:
        """Analyze wardrobe gaps and return recommendations."""
        gaps = {
            "missing_colors": [],
            "underrepresented_categories": [],
            "seasonal_gaps": [],
            "quantity_gaps": [],
            "recommendations": []
        }
        
        # 1. Color Gap Analysis
        gaps["missing_colors"] = self._find_missing_colors()
        
        # 2. Category Analysis
        gaps["underrepresented_categories"] = self._find_underrepresented_categories()
        
        # 3. Seasonal Gaps
        gaps["seasonal_gaps"] = self._find_seasonal_gaps()
        
        # 4. Quantity Gaps
        gaps["quantity_gaps"] = self._find_quantity_gaps()
        
        # 5. Generate Recommendations
        gaps["recommendations"] = self._generate_recommendations(gaps)
        
        return gaps
    
    def _find_missing_colors(self) -> List[str]:
        """Find colors that are missing or underrepresented."""
        common_colors = ["black", "white", "blue", "red", "green", "yellow", 
                        "orange", "pink", "purple", "brown", "gray", "beige"]
        
        existing_colors = set(self.wardrobe["color_distribution"].keys())
        missing = [c for c in common_colors if c not in existing_colors]
        
        # Also check for underrepresented colors (only 1-2 items)
        underrepresented = [
            color for color, count in self.wardrobe["color_distribution"].items()
            if count <= 2 and color in common_colors
        ]
        
        return list(set(missing + underrepresented))
    
    def _find_underrepresented_categories(self) -> List[str]:
        """Find categories with very few items."""
        underrepresented = []
        
        for category in ["tops", "bottoms", "outerwear"]:
            total_items = sum(
                item_data["count"] 
                for item_data in self.wardrobe[category].values()
            )
            
            min_expected = {"tops": 5, "bottoms": 4, "outerwear": 2}[category]
            
            if total_items < min_expected:
                underrepresented.append(category)
        
        return underrepresented
    
    def _find_seasonal_gaps(self) -> List[str]:
        """Find seasonal clothing gaps."""
        seasonal_gaps = []
        
        # Winter needs
        if self.season in ["winter", "autumn"]:
            outerwear_items = sum(
                item_data["count"] 
                for item_data in self.wardrobe["outerwear"].values()
            )
            if outerwear_items < 2:
                seasonal_gaps.append("warm_outerwear")
            
            # Check for warm items
            warm_categories = ["sweater", "hoodie", "coat", "jacket"]
            has_warm = any(
                cat in self.wardrobe["outerwear"] 
                for cat in warm_categories
            )
            if not has_warm:
                seasonal_gaps.append("warm_clothing")
        
        # Summer needs
        elif self.season in ["summer", "spring"]:
            summer_items = ["t-shirt", "shorts", "tank", "top"]
            has_summer = any(
                any(item in cat for item in summer_items)
                for cat in self.wardrobe["tops"].keys()
            )
            if not has_summer:
                seasonal_gaps.append("summer_clothing")
        
        return seasonal_gaps
    
    def _find_quantity_gaps(self) -> List[Dict]:
        """Find categories with insufficient quantity."""
        quantity_gaps = []
        
        # Expected minimum quantities
        expected = {
            "tops": 5,
            "bottoms": 4,
            "outerwear": 2
        }
        
        for category, min_count in expected.items():
            current_count = sum(
                item_data["count"] 
                for item_data in self.wardrobe[category].values()
            )
            
            if current_count < min_count:
                quantity_gaps.append({
                    "category": category,
                    "current": current_count,
                    "recommended": min_count,
                    "needed": min_count - current_count
                })
        
        return quantity_gaps
    
    def _generate_recommendations(self, gaps: Dict) -> List[Dict]:
        """Generate prioritized shopping recommendations."""
        recommendations = []
        priority = 1
        
        # HIGH PRIORITY: Seasonal gaps
        if gaps["seasonal_gaps"]:
            for gap in gaps["seasonal_gaps"]:
                if gap == "warm_outerwear":
                    recommendations.append({
                        "priority": "HIGH",
                        "item": "Winter Coat or Jacket",
                        "reason": "Essential for winter season",
                        "suggested_color": "Any neutral color (black, gray, navy)",
                        "category": "outerwear",
                        "priority_num": priority
                    })
                    priority += 1
                elif gap == "warm_clothing":
                    recommendations.append({
                        "priority": "HIGH",
                        "item": "Sweater or Hoodie",
                        "reason": "Needed for cold weather",
                        "suggested_color": "Any color",
                        "category": "outerwear",
                        "priority_num": priority
                    })
                    priority += 1
        
        # HIGH PRIORITY: Critical quantity gaps
        for qgap in gaps["quantity_gaps"]:
            if qgap["needed"] >= 2:
                recommendations.append({
                    "priority": "HIGH",
                    "item": f"2-3 {qgap['category'].title()}",
                    "reason": f"Only {qgap['current']} {qgap['category']}, need {qgap['recommended']} minimum",
                    "suggested_color": gaps["missing_colors"][:2] if gaps["missing_colors"] else "Any color",
                    "category": qgap["category"],
                    "priority_num": priority
                })
                priority += 1
        
        # MEDIUM PRIORITY: Missing colors
        if gaps["missing_colors"]:
            missing_colors_str = ", ".join(gaps["missing_colors"][:3])
            recommendations.append({
                "priority": "MEDIUM",
                "item": f"Tops in {missing_colors_str}",
                "reason": "Add color variety to wardrobe",
                "suggested_color": missing_colors_str,
                "category": "tops",
                "priority_num": priority
            })
            priority += 1
        
        # MEDIUM PRIORITY: Underrepresented categories
        for cat in gaps["underrepresented_categories"]:
            recommendations.append({
                "priority": "MEDIUM",
                "item": f"More {cat} items",
                "reason": f"{cat.title()} category needs more variety",
                "suggested_color": "Any color",
                "category": cat,
                "priority_num": priority
            })
            priority += 1
        
        # LOW PRIORITY: Style variety
        recommendations.append({
            "priority": "LOW",
            "item": "Statement piece (bright color or pattern)",
            "reason": "Add personality to wardrobe",
            "suggested_color": "Bright colors (yellow, pink, orange)",
            "category": "tops",
            "priority_num": priority
        })
        
        return recommendations


# ==========================
# Main Shopping Recommender
# ==========================
class ShoppingRecommender:
    """Main class for generating shopping recommendations."""
    
    def __init__(self, images_root: Path, caption_cache: Dict[str, str] = None):
        self.images_root = images_root
        self.caption_cache = caption_cache or {}
        self.analyzer = None
        self.gap_analyzer = None
        
    def generate_recommendations(self, season: str = "summer") -> Dict:
        """
        Generate complete shopping recommendations.
        
        Args:
            season: Current season (summer/winter/spring/autumn)
            
        Returns:
            Dictionary with wardrobe analysis and recommendations
        """
        # Step 1: Analyze current wardrobe
        self.analyzer = WardrobeAnalyzer(self.images_root, self.caption_cache)
        wardrobe_data = self.analyzer.scan_wardrobe()
        
        # Step 2: Analyze gaps
        self.gap_analyzer = GapAnalyzer(wardrobe_data, season)
        gaps = self.gap_analyzer.analyze_gaps()
        
        # Step 3: Compile results
        results = {
            "wardrobe_summary": self._format_wardrobe_summary(wardrobe_data),
            "gap_analysis": self._format_gap_analysis(gaps),
            "recommendations": gaps["recommendations"],
            "shopping_list": self._format_shopping_list(gaps["recommendations"])
        }
        
        return results
    
    def _format_wardrobe_summary(self, wardrobe: Dict) -> str:
        """Format wardrobe summary for display."""
        summary = "## 📊 Current Wardrobe Analysis\n\n"
        
        # Category breakdown
        for category in ["tops", "bottoms", "outerwear"]:
            total = sum(item["count"] for item in wardrobe[category].values())
            summary += f"**{category.title()}**: {total} items\n"
            for item_name, item_data in wardrobe[category].items():
                if item_data["unique_colors"]:
                    colors_str = ", ".join(item_data["unique_colors"][:5])
                    summary += f"  - {item_name}: {item_data['count']} items ({colors_str})\n"
                else:
                    summary += f"  - {item_name}: {item_data['count']} items (colors not detected)\n"
            summary += "\n"
        
        # Color distribution
        summary += "**Color Distribution**:\n"
        top_colors = wardrobe["color_distribution"].most_common(5)
        if top_colors:
            for color, count in top_colors:
                summary += f"  - {color.capitalize()}: {count} items\n"
        else:
            summary += "  - No colors detected (filenames may not contain color names)\n"
        
        return summary
    
    def _format_gap_analysis(self, gaps: Dict) -> str:
        """Format gap analysis for display."""
        analysis = "## 🔍 Wardrobe Gap Analysis\n\n"
        
        if gaps["missing_colors"]:
            analysis += f"**Missing Colors**: {', '.join(gaps['missing_colors'][:5])}\n\n"
        
        if gaps["underrepresented_categories"]:
            analysis += f"**Underrepresented Categories**: {', '.join(gaps['underrepresented_categories'])}\n\n"
        
        if gaps["seasonal_gaps"]:
            analysis += f"**Seasonal Needs**: {', '.join(gaps['seasonal_gaps'])}\n\n"
        
        if gaps["quantity_gaps"]:
            analysis += "**Quantity Gaps**:\n"
            for qgap in gaps["quantity_gaps"]:
                analysis += f"  - {qgap['category']}: {qgap['current']}/{qgap['recommended']} items\n"
        
        return analysis
    
    def _format_shopping_list(self, recommendations: List[Dict]) -> str:
        """Format shopping list for display."""
        shopping_list = "## 🛍️ Shopping Recommendations\n\n"
        
        # Group by priority
        high_priority = [r for r in recommendations if r["priority"] == "HIGH"]
        medium_priority = [r for r in recommendations if r["priority"] == "MEDIUM"]
        low_priority = [r for r in recommendations if r["priority"] == "LOW"]
        
        if high_priority:
            shopping_list += "### 🔴 HIGH PRIORITY\n\n"
            for i, rec in enumerate(high_priority, 1):
                shopping_list += f"{i}. **{rec['item']}**\n"
                shopping_list += f"   - Reason: {rec['reason']}\n"
                shopping_list += f"   - Suggested Color: {rec['suggested_color']}\n\n"
        
        if medium_priority:
            shopping_list += "### 🟡 MEDIUM PRIORITY\n\n"
            for i, rec in enumerate(medium_priority, 1):
                shopping_list += f"{i}. **{rec['item']}**\n"
                shopping_list += f"   - Reason: {rec['reason']}\n"
                shopping_list += f"   - Suggested Color: {rec['suggested_color']}\n\n"
        
        if low_priority:
            shopping_list += "### 🟢 LOW PRIORITY\n\n"
            for i, rec in enumerate(low_priority, 1):
                shopping_list += f"{i}. **{rec['item']}**\n"
                shopping_list += f"   - Reason: {rec['reason']}\n"
                shopping_list += f"   - Suggested Color: {rec['suggested_color']}\n\n"
        
        return shopping_list


# ==========================
# Gradio Integration Function
# ==========================
def generate_shopping_recommendations(images_root: str, season: str, caption_cache: Dict = None, 
                                     caption_cache_path: str = None) -> Tuple[str, str, str]:
    """
    Main function to call from Gradio.
    
    Args:
        images_root: Path to clothing images folder
        season: Current season
        caption_cache: Optional BLIP caption cache (dict)
        caption_cache_path: Optional path to BLIP caption JSON file
        
    Returns:
        Tuple of (wardrobe_summary, gap_analysis, shopping_list)
    """
    try:
        # Load caption cache if not provided or empty; then merge with provided cache
        if not caption_cache:
            if caption_cache_path:
                caption_cache = load_blip_caption_cache(caption_cache_path)
            else:
                # Try to auto-detect cache file based on images_root
                root_lower = str(images_root).lower()
                # Prefer specific gendered caches if they exist
                preferred_paths = []
                if "men" in root_lower or "male" in root_lower:
                    preferred_paths = ["blip_captions_male.json", "blip_captions_cache.json"]
                elif "women" in root_lower or "female" in root_lower or "clothing_images" in root_lower:
                    preferred_paths = ["blip_captions_female.json", "blip_captions_cache.json"]
                else:
                    preferred_paths = ["blip_captions_cache.json", "blip_captions_male.json", "blip_captions_female.json"]

                loaded = {}
                for p in preferred_paths:
                    loaded = load_blip_caption_cache(p)
                    if loaded:
                        caption_cache = loaded
                        break
                if not loaded:
                    caption_cache = {}
        else:
            # Normalize any provided in-memory cache keys
            caption_cache = _normalize_caption_cache_keys(caption_cache)
        
        recommender = ShoppingRecommender(Path(images_root), caption_cache)
        results = recommender.generate_recommendations(season)
        
        return (
            results["wardrobe_summary"],
            results["gap_analysis"],
            results["shopping_list"]
        )
    except Exception as e:
        error_msg = f"❌ Error generating recommendations: {str(e)}"
        return error_msg, error_msg, error_msg


# ==========================
# Test Function
# ==========================
if __name__ == "__main__":
    # Test with male images
    print("Testing with male images...")
    results = generate_shopping_recommendations(
        images_root="clothing_images_men",
        season="winter",
        caption_cache={}
    )
    
    print("\n" + "="*60)
    print(results[0])  # Wardrobe summary
    print("\n" + "="*60)
    print(results[1])  # Gap analysis
    print("\n" + "="*60)
    print(results[2])  # Shopping list

