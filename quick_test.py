"""
Quick test for the dynamic shopping system
"""

from dynamic_shopping_recommender import generate_dynamic_shopping_recommendations

def test_system():
    print("🚀 Testing Dynamic Shopping System...")
    
    try:
        # Test with men's clothing
        wardrobe_summary, gap_analysis, shopping_list, product_images, product_links = generate_dynamic_shopping_recommendations(
            images_root="clothing_images_men",
            season="summer"
        )
        
        print("\n" + "="*60)
        print("WARDROBE SUMMARY:")
        print("="*60)
        print(wardrobe_summary)
        
        print("\n" + "="*60)
        print("GAP ANALYSIS:")
        print("="*60)
        print(gap_analysis)
        
        print("\n" + "="*60)
        print("SHOPPING RECOMMENDATIONS:")
        print("="*60)
        print(shopping_list)
        
        print("\n" + "="*60)
        print("PRODUCT IMAGES:")
        print("="*60)
        print(f"Found {len(product_images)} product images")
        for i, img in enumerate(product_images[:5], 1):
            print(f"{i}. {img}")
        
        print("\n" + "="*60)
        print("PRODUCT LINKS:")
        print("="*60)
        print(f"Found {len(product_links)} product links")
        for i, link in enumerate(product_links[:5], 1):
            print(f"{i}. {link}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_system()
