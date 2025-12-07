"""
Test script for the dynamic shopping recommendation system
"""

from dynamic_shopping_recommender import generate_dynamic_shopping_recommendations
from clothing_web_scraper import ClothingWebScraper

def test_web_scraper():
    """Test the web scraper functionality"""
    print("🔍 Testing Web Scraper...")
    scraper = ClothingWebScraper()
    
    # Test scraping Outfitters men's shirts
    print("Scraping Outfitters men's shirts...")
    men_shirts = scraper.scrape_outfitters_men_shirts()
    print(f"Found {len(men_shirts)} men's shirts")
    
    if men_shirts:
        print("\nSample product:")
        sample = men_shirts[0]
        print(f"Name: {sample.get('name', 'N/A')}")
        print(f"Price: {sample.get('price', 'N/A')}")
        print(f"Colors: {sample.get('colors', [])}")
        print(f"Website: {sample.get('website', 'N/A')}")
        if sample.get('product_url'):
            print(f"URL: {sample['product_url']}")
    
    # Test color filtering
    print("\n🔍 Testing color filtering...")
    blue_products = scraper.get_products_by_color("blue", "men")
    print(f"Found {len(blue_products)} blue men's products")
    
    return scraper

def test_dynamic_recommender(scraper=None):
    """Test the dynamic shopping recommender"""
    print("\n🛍️ Testing Dynamic Shopping Recommender...")
    
    # Test with men's clothing
    print("Generating recommendations for men...")
    wardrobe_summary, gap_analysis, shopping_list, product_images, product_links = generate_dynamic_shopping_recommendations(
        images_root="clothing_images_men",
        season="summer"
    )
    
    print("\n" + "="*50)
    print("WARDROBE SUMMARY:")
    print("="*50)
    print(wardrobe_summary)
    
    print("\n" + "="*50)
    print("GAP ANALYSIS:")
    print("="*50)
    print(gap_analysis)
    
    print("\n" + "="*50)
    print("SHOPPING RECOMMENDATIONS:")
    print("="*50)
    print(shopping_list)
    
    print("\n" + "="*50)
    print("PRODUCT IMAGES:")
    print("="*50)
    print(f"Found {len(product_images)} product images")
    for i, img in enumerate(product_images[:3], 1):
        print(f"{i}. {img}")
    
    print("\n" + "="*50)
    print("PRODUCT LINKS:")
    print("="*50)
    print(f"Found {len(product_links)} product links")
    for i, link in enumerate(product_links[:3], 1):
        print(f"{i}. {link}")

def main():
    """Run all tests"""
    print("🚀 Starting Dynamic Shopping System Tests...")
    
    try:
        # Test web scraper
        scraper = test_web_scraper()
        
        # Save scraped data
        scraper.save_to_json("test_scraped_data.json")
        print("\n✅ Web scraper test completed successfully!")
        
    except Exception as e:
        print(f"❌ Web scraper test failed: {e}")
    
    try:
        # Test dynamic recommender
        test_dynamic_recommender(scraper)
        print("\n✅ Dynamic recommender test completed successfully!")
        
    except Exception as e:
        print(f"❌ Dynamic recommender test failed: {e}")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    main()
