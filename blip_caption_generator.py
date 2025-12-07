"""
🖼️ BLIP Caption Generator
Scans all images and generates captions using BLIP model
Stores captions for easy access by shopping recommender
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from tqdm import tqdm

# BLIP imports
try:
    import torch
    from transformers import BlipProcessor, BlipForConditionalGeneration
    from PIL import Image
    BLIP_AVAILABLE = True
except ImportError:
    BLIP_AVAILABLE = False
    print("⚠️ BLIP not available. Install: pip install transformers torch pillow")

VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


class BLIPCaptionGenerator:
    """Generate and store BLIP captions for all clothing images."""
    
    def __init__(self, blip_model_path: str = "blip_finetunedggdata"):
        self.blip_model_path = blip_model_path
        self.processor = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.caption_cache = {}
        
    def load_model(self):
        """Load BLIP model."""
        if not BLIP_AVAILABLE:
            raise ImportError("BLIP dependencies not installed")
        
        print(f"🔄 Loading BLIP model from: {self.blip_model_path}")
        try:
            self.processor = BlipProcessor.from_pretrained(self.blip_model_path)
            self.model = BlipForConditionalGeneration.from_pretrained(self.blip_model_path)
            self.model.to(self.device)
            print(f"✅ BLIP model loaded successfully on {self.device}")
        except Exception as e:
            print(f"❌ Error loading BLIP model: {e}")
            raise
    
    def generate_caption(self, image_path: str, item_type: str = "clothing") -> str:
        """Generate caption for a single image."""
        if not self.model or not self.processor:
            return ""
        
        try:
            img = Image.open(image_path).convert("RGB")
            
            # Create prompt for better fashion-related captions
            prompt = f"a studio product photo of a {item_type}"
            
            inputs = self.processor(img, text=prompt, return_tensors="pt").to(self.device)
            out = self.model.generate(**inputs, max_new_tokens=30)
            caption = self.processor.decode(out[0], skip_special_tokens=True)
            
            return caption
        except Exception as e:
            print(f"⚠️ Error generating caption for {image_path}: {e}")
            return ""
    
    def scan_and_generate_captions(self, images_root: str, save_path: str = "blip_captions_cache.json"):
        """
        Scan all images and generate captions.
        
        Args:
            images_root: Path to clothing images folder
            save_path: Path to save caption cache JSON file
        """
        images_root = Path(images_root)
        if not images_root.exists():
            print(f"❌ Images folder not found: {images_root}")
            return
        
        print(f"🔍 Scanning images in: {images_root}")
        
        # Find all image files
        image_files = []
        for folder in images_root.iterdir():
            if not folder.is_dir():
                continue
            if folder.name.lower() in ["data", "none"]:
                continue
            
            for img_file in folder.iterdir():
                if img_file.suffix.lower() in VALID_EXTS:
                    image_files.append((img_file, folder.name))
        
        print(f"📸 Found {len(image_files)} images to process")
        
        # Generate captions with progress bar
        for img_file, item_type in tqdm(image_files, desc="Generating captions"):
            img_path = str(img_file)
            caption = self.generate_caption(img_path, item_type)
            self.caption_cache[img_path] = caption.lower()  # Store lowercase
        
        # Save to JSON file
        self.save_captions(save_path)
        print(f"✅ Generated {len(self.caption_cache)} captions")
        print(f"💾 Saved captions to: {save_path}")
    
    def save_captions(self, save_path: str):
        """Save caption cache to JSON file."""
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.caption_cache, f, indent=2, ensure_ascii=False)
    
    def load_captions(self, load_path: str = "blip_captions_cache.json") -> Dict[str, str]:
        """Load caption cache from JSON file."""
        load_path = Path(load_path)
        if not load_path.exists():
            print(f"⚠️ Caption cache not found: {load_path}")
            return {}
        
        with open(load_path, 'r', encoding='utf-8') as f:
            self.caption_cache = json.load(f)
        
        print(f"✅ Loaded {len(self.caption_cache)} captions from {load_path}")
        return self.caption_cache
    
    def get_caption(self, image_path: str) -> str:
        """Get caption for an image (from cache)."""
        return self.caption_cache.get(str(image_path), "")


def generate_all_captions(images_root: str, blip_model_path: str = "blip_finetunedggdata", 
                         save_path: str = "blip_captions_cache.json"):
    """
    Main function to generate captions for all images.
    
    Args:
        images_root: Path to clothing images folder (e.g., "clothing_images_men")
        blip_model_path: Path to BLIP model folder
        save_path: Path to save caption cache
    
    Returns:
        Dictionary of {image_path: caption}
    """
    generator = BLIPCaptionGenerator(blip_model_path)
    generator.load_model()
    generator.scan_and_generate_captions(images_root, save_path)
    return generator.caption_cache


def load_caption_cache(load_path: str = "blip_captions_cache.json") -> Dict[str, str]:
    """
    Load existing caption cache.
    
    Args:
        load_path: Path to caption cache JSON file
    
    Returns:
        Dictionary of {image_path: caption}
    """
    generator = BLIPCaptionGenerator()
    return generator.load_captions(load_path)


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("🖼️ BLIP Caption Generator")
    print("=" * 60)
    
    # Generate captions for male clothing
    print("\n📸 Generating captions for MALE clothing...")
    male_captions = generate_all_captions(
        images_root="clothing_images_men",
        blip_model_path="blip_finetunedggdata",
        save_path="blip_captions_male.json"
    )
    
    # Generate captions for female clothing
    print("\n📸 Generating captions for FEMALE clothing...")
    female_captions = generate_all_captions(
        images_root="clothing_images",
        blip_model_path="blip_finetunedggdata",
        save_path="blip_captions_female.json"
    )
    
    print("\n✅ Done! Caption files created:")
    print("   - blip_captions_male.json")
    print("   - blip_captions_female.json")

