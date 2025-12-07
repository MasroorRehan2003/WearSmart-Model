"""
🚀 Quick Script to Generate BLIP Captions
Run this once to generate captions for all images
"""

from blip_caption_generator import generate_all_captions

if __name__ == "__main__":
    print("=" * 70)
    print("🖼️  BLIP Caption Generator")
    print("=" * 70)
    print()
    
    # Generate captions for MALE clothing
    print("📸 Step 1/2: Generating captions for MALE clothing...")
    print("-" * 70)
    male_captions = generate_all_captions(
        images_root="clothing_images_men",
        blip_model_path="blip_finetunedggdata",
        save_path="blip_captions_male.json"
    )
    print(f"✅ Generated {len(male_captions)} captions for male clothing")
    print()
    
    # Generate captions for FEMALE clothing
    print("📸 Step 2/2: Generating captions for FEMALE clothing...")
    print("-" * 70)
    female_captions = generate_all_captions(
        images_root="clothing_images",
        blip_model_path="blip_finetunedggdata",
        save_path="blip_captions_female.json"
    )
    print(f"✅ Generated {len(female_captions)} captions for female clothing")
    print()
    
    print("=" * 70)
    print("✅ ALL DONE!")
    print("=" * 70)
    print()
    print("📁 Caption files created:")
    print("   ✓ blip_captions_male.json")
    print("   ✓ blip_captions_female.json")
    print()
    print("🎉 You can now use the shopping recommender!")
    print("   The system will automatically load these captions.")

