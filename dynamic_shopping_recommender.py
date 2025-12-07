"""
Dynamic Shopping Recommender using Real Web Data
Integrates with web scraper to provide real product recommendations
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from clothing_web_scraper import ClothingWebScraper
import logging

logger = logging.getLogger(__name__)

class DynamicShoppingRecommender:
    """Generates shopping recommendations using real web data"""
    
    def __init__(self, images_root: str, caption_cache: Dict = None, gender: str = "men", preferred_category: Optional[str] = None):
        self.images_root = Path(images_root)
        self.caption_cache = caption_cache or {}
        self.web_scraper = ClothingWebScraper()
        self.gender = (gender or "men").lower()
        self.preferred_category = (preferred_category or "").strip().lower()
        
        # Load or scrape web data
        self.web_data = self.web_scraper.load_from_json()
        if not self.web_data or all(len(products) == 0 for products in self.web_data.values()):
            logger.info("No cached web data found or empty cache, scraping fresh data...")
            self.web_data = self.web_scraper.scrape_all_websites()
            self.web_scraper.save_to_json()
        else:
            # Ensure gender-specific data exists; if missing for requested gender, scrape that slice now
            try:
                if self.gender == "women":
                    has_women = any(k.startswith("outfitters_women") and len(v) > 0 for k, v in self.web_data.items())
                    if not has_women:
                        logger.info("No women's products in cache; scraping Outfitters women now...")
                        women_products = self.web_scraper.scrape_outfitters_women_shirts()
                        self.web_data["outfitters_women"] = women_products
                        self.web_scraper.scraped_data = self.web_data
                        self.web_scraper.save_to_json()
                elif self.gender == "men":
                    has_men = any(k.startswith("outfitters_men") and len(v) > 0 for k, v in self.web_data.items())
                    if not has_men:
                        logger.info("No men's products in cache; scraping Outfitters men now...")
                        men_products = self.web_scraper.scrape_outfitters_men_shirts()
                        self.web_data["outfitters_men"] = men_products
                        self.web_scraper.scraped_data = self.web_data
                        self.web_scraper.save_to_json()
                # If preferred_category requested, ensure that collection exists
                if self.preferred_category:
                    ensured = self.web_scraper.ensure_outfitters_category(self.gender, self.preferred_category)
                    if ensured:
                        # Reload from scraper's latest cache
                        self.web_data = self.web_scraper.scraped_data
            except Exception:
                pass
    
    def analyze_wardrobe_gaps(self, season: str) -> Dict:
        """Analyze wardrobe gaps using both local images and web data"""
        # Get local wardrobe analysis (simplified version)
        local_analysis = self._analyze_local_wardrobe()
        
        # Get available web products
        web_products = self._get_available_products()
        
        # Find gaps and recommendations
        gaps = self._identify_gaps(local_analysis, web_products, season)
        
        return {
            'local_wardrobe': local_analysis,
            'available_products': web_products,
            'gaps': gaps
        }
    
    def _analyze_local_wardrobe(self) -> Dict:
        """Analyze local wardrobe (simplified version)"""
        wardrobe = {
            'tops': 0,
            'bottoms': 0,
            'outerwear': 0,
            'colors': [],
            'categories': {}
        }
        
        # Count items in each category
        for item_folder in self.images_root.iterdir():
            if not item_folder.is_dir():
                continue
                
            category = self._categorize_item(item_folder.name)
            if category:
                wardrobe[category] += 1
                wardrobe['categories'][item_folder.name] = len(list(item_folder.iterdir()))
        
        return wardrobe
    
    def _categorize_item(self, item_name: str) -> Optional[str]:
        """Categorize item into tops, bottoms, or outerwear"""
        item_lower = item_name.lower()
        
        top_items = {'shirt', 't-shirt', 'kurta', 'sweater', 'top', 'blouse', 'tank', 'crop'}
        bottom_items = {'pants', 'jeans', 'trousers', 'shorts', 'leggings', 'skirt', 'capris'}
        outerwear_items = {'jacket', 'coat', 'blazer', 'hoodie', 'sweater', 'cardigan', 'dupatta'}
        
        if any(item in item_lower for item in top_items):
            return 'tops'
        elif any(item in item_lower for item in bottom_items):
            return 'bottoms'
        elif any(item in item_lower for item in outerwear_items):
            return 'outerwear'
        
        return None
    
    def _get_available_products(self) -> Dict[str, List[Dict]]:
        """Get available products from web scraping"""
        all_products = []
        
        for website, products in self.web_data.items():
            all_products.extend(products)
        
        # Group by category and gender
        categorized = {
            'men_tops': [],
            'men_bottoms': [],
            'men_outerwear': [],
            'women_tops': [],
            'women_bottoms': [],
            'women_outerwear': []
        }
        
        for product in all_products:
            gender = product.get('gender', 'men')
            category = product.get('category', 'general')
            
            # Map categories to our system
            if category in ['shirts', 't-shirt', 'kurta', 'sweater', 'top', 'blouse']:
                category = 'tops'
            elif category in ['pants', 'jeans', 'trousers', 'shorts', 'leggings', 'skirt']:
                category = 'bottoms'
            elif category in ['jacket', 'coat', 'blazer', 'hoodie', 'cardigan', 'dupatta']:
                category = 'outerwear'
            else:
                category = 'tops'  # Default to tops for unknown categories
            
            # If preferred_category is set, skip mismatches
            if self.preferred_category:
                if category != 'tops' and self.preferred_category in {'shirt','shirts','t-shirt','tshirts','tee','tees','kurta','kurtas','top','tops','blouse','blouses','sweater','sweaters'}:
                    pass  # only tops match will be included below
                # Map preferred to bucket
                pref_map = {
                    'shirt':'tops','shirts':'tops','t-shirt':'tops','tshirts':'tops','tee':'tops','tees':'tops',
                    'kurta':'tops','kurtas':'tops','top':'tops','tops':'tops','blouse':'tops','blouses':'tops',
                    'sweater':'tops','sweaters':'tops',
                    'jeans':'bottoms','trousers':'bottoms','pants':'bottoms','shorts':'bottoms','leggings':'bottoms','skirt':'bottoms','skirts':'bottoms','capris':'bottoms',
                    'jacket':'outerwear','jackets':'outerwear','coat':'outerwear','coats':'outerwear','hoodie':'outerwear','hoodies':'outerwear','blazer':'outerwear','blazers':'outerwear','dupatta':'outerwear','dupattas':'outerwear'
                }
                desired_bucket = pref_map.get(self.preferred_category)
                if desired_bucket and category != desired_bucket:
                    continue

            key = f"{gender}_{category}"
            if key in categorized:
                categorized[key].append(product)
        
        # Filter by gender for the caller
        filtered: Dict[str, List[Dict]] = {}
        for key, items in categorized.items():
            if key.startswith(f"{self.gender}_"):
                filtered[key] = items
        return filtered
    
    def _identify_gaps(self, local_wardrobe: Dict, web_products: Dict, season: str) -> Dict:
        """Identify gaps between local wardrobe and available products"""
        gaps = {
            'missing_colors': [],
            'missing_categories': [],
            'seasonal_needs': [],
            'recommendations': []
        }
        
        # Analyze color gaps
        available_colors = set()
        for products in web_products.values():
            for product in products:
                for c in self._clean_colors(product.get('colors', [])):
                    available_colors.add(c)
        
        local_colors = set(local_wardrobe.get('colors', []))
        gaps['missing_colors'] = list(available_colors - local_colors)
        
        # Analyze category gaps
        local_categories = set(local_wardrobe.get('categories', {}).keys())
        available_categories = set()
        for products in web_products.values():
            for product in products:
                available_categories.add(product.get('category', ''))
        
        gaps['missing_categories'] = list(available_categories - local_categories)
        
        # Seasonal recommendations
        gaps['seasonal_needs'] = self._get_seasonal_recommendations(season, web_products)
        
        return gaps

    def _clean_colors(self, colors: List[str]) -> List[str]:
        """Remove sizes/meta like XS/S/M/L, 'X Colors', and non-color descriptors."""
        cleaned: List[str] = []
        for raw in colors or []:
            if not raw:
                continue
            t = raw.strip()
            tl = t.lower()
            if len(tl) > 40:
                continue
            if tl in {"xs","s","m","l","xl","xxl","xxxl","one size"}:
                continue
            if "fit" in tl or "women" in tl or "men" in tl:
                continue
            if re.search(r"\b\d+\s*colors?\b", tl):
                continue
            cleaned.append(t)
        return cleaned
    
    def _get_seasonal_recommendations(self, season: str, web_products: Dict) -> List[Dict]:
        """Get seasonal product recommendations"""
        seasonal_keywords = {
            'summer': ['cotton', 'linen', 'light', 'short', 'tank'],
            'winter': ['wool', 'warm', 'thick', 'jacket', 'sweater'],
            'spring': ['light', 'colorful', 'fresh'],
            'autumn': ['layered', 'warm', 'earth']
        }
        
        recommendations = []
        keywords = seasonal_keywords.get(season.lower(), [])
        
        for products in web_products.values():
            for product in products:
                product_text = f"{product.get('name', '')} {' '.join(product.get('colors', []))}".lower()
                if any(keyword in product_text for keyword in keywords):
                    recommendations.append(product)
        
        return recommendations[:10]  # Limit to top 10
    
    def generate_shopping_recommendations(self, season: str) -> Tuple[str, str, str, List[str], List[str]]:
        """Generate comprehensive shopping recommendations with images and links"""
        try:
            # Analyze wardrobe gaps
            analysis = self.analyze_wardrobe_gaps(season)
            
            # Generate formatted outputs
            wardrobe_summary = self._format_wardrobe_summary(analysis['local_wardrobe'])
            gap_analysis = self._format_gap_analysis(analysis['gaps'])
            shopping_list, product_images, product_links = self._format_shopping_list(analysis['gaps'], analysis['available_products'])
            
            return wardrobe_summary, gap_analysis, shopping_list, product_images, product_links
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            error_msg = f"❌ Error generating recommendations: {str(e)}"
            return error_msg, error_msg, error_msg, [], []
    
    def _format_wardrobe_summary(self, wardrobe: Dict) -> str:
        """Format wardrobe summary"""
        summary = "📊 **Current Wardrobe Analysis**\n\n"
        
        summary += f"**Tops:** {wardrobe.get('tops', 0)} items\n"
        summary += f"**Bottoms:** {wardrobe.get('bottoms', 0)} items\n"
        summary += f"**Outerwear:** {wardrobe.get('outerwear', 0)} items\n\n"
        
        if wardrobe.get('categories'):
            summary += "**Categories:**\n"
            for category, count in wardrobe['categories'].items():
                summary += f"- {category}: {count} items\n"
        
        return summary
    
    def _format_gap_analysis(self, gaps: Dict) -> str:
        """Format gap analysis"""
        analysis = "🔍 **Wardrobe Gap Analysis**\n\n"
        
        if gaps.get('missing_colors'):
            analysis += f"**Missing Colors:** {', '.join(gaps['missing_colors'][:10])}\n\n"
        
        if gaps.get('missing_categories'):
            analysis += f"**Missing Categories:** {', '.join(gaps['missing_categories'][:5])}\n\n"
        
        if gaps.get('seasonal_needs'):
            analysis += f"**Seasonal Needs:** {len(gaps['seasonal_needs'])} items found\n\n"
        
        return analysis
    
    def _format_shopping_list(self, gaps: Dict, web_products: Dict) -> Tuple[str, List[str], List[str]]:
        """Format shopping recommendations with real products and return images/links"""
        shopping_list = "🛍️ **Shopping Recommendations**\n\n"
        product_images: List[str] = []
        product_links: List[str] = []
        seen_products: set = set()      # dedupe by product_url
        seen_images: set = set()        # dedupe by image_url
        
        # High priority recommendations
        shopping_list += "🔴 **HIGH PRIORITY**\n"
        
        # Get top products from each category
        for category, products in web_products.items():
            if products:
                added_in_category = 0
                for product in products:
                    # dedupe by product url or name
                    key = (product.get('product_url') or '').strip() or product.get('name','').strip()
                    if not key or key in seen_products:
                        continue
                    seen_products.add(key)
                    shopping_list += f"**{product.get('name', 'Product')}**\n"
                    shopping_list += f"💰 {product.get('price', 'Price not available')}\n"
                    
                    # Clean up colors display
                    clean_colors = self._clean_colors(product.get('colors', []))
                    
                    if clean_colors:
                        shopping_list += f"🎨 Colors: {', '.join(clean_colors[:3])}\n"
                    else:
                        shopping_list += f"🎨 Colors: Not specified\n"
                    
                    shopping_list += f"🏪 {product.get('website', 'Unknown store')}\n"
                    
                    # Add image and link
                    img_url = (product.get('image_url') or '').strip()
                    if img_url and img_url not in seen_images:
                        seen_images.add(img_url)
                        product_images.append(img_url)
                    prod_url = (product.get('product_url') or '').strip()
                    if prod_url:
                        product_links.append(prod_url)
                        shopping_list += f"🔗 [View Product]({prod_url})\n"
                    shopping_list += "\n"
                    added_in_category += 1
                    if added_in_category >= 3:  # limit per category
                        break
        
        # Seasonal recommendations
        if gaps.get('seasonal_needs'):
            shopping_list += "🟡 **SEASONAL RECOMMENDATIONS**\n"
            added_seasonal = 0
            for product in gaps['seasonal_needs']:
                shopping_list += f"**{product.get('name', 'Product')}**\n"
                shopping_list += f"💰 {product.get('price', 'Price not available')}\n"
                
                # Clean up colors display
                clean_colors = self._clean_colors(product.get('colors', []))
                
                if clean_colors:
                    shopping_list += f"🎨 Colors: {', '.join(clean_colors[:3])}\n"
                else:
                    shopping_list += f"🎨 Colors: Not specified\n"
                
                shopping_list += f"🏪 {product.get('website', 'Unknown store')}\n"
                
                # Add image and link
                img_url = (product.get('image_url') or '').strip()
                if img_url and img_url not in seen_images:
                    seen_images.add(img_url)
                    product_images.append(img_url)
                prod_url = (product.get('product_url') or '').strip()
                if prod_url:
                    product_links.append(prod_url)
                    shopping_list += f"🔗 [View Product]({prod_url})\n"
                shopping_list += "\n"
                added_seasonal += 1
                if added_seasonal >= 5:
                    break
        
        return shopping_list, product_images, product_links

def generate_dynamic_shopping_recommendations(images_root: str, season: str, caption_cache: Dict = None, gender: str = "men", preferred_category: Optional[str] = None) -> Tuple[str, str, str, List[str], List[str]]:
    """Main function to generate dynamic shopping recommendations"""
    try:
        recommender = DynamicShoppingRecommender(images_root, caption_cache, gender=gender)
        # If a preferred category is provided, reduce web_data to that category family
        if preferred_category:
            cat = preferred_category.strip().lower()
            # Map input to our canonical buckets
            tops_aliases = {"shirt","shirts","t-shirt","tshirts","tee","tees","kurta","kurtas","top","tops","blouse","blouses","sweater","sweaters"}
            bottoms_aliases = {"pants","trousers","jeans","shorts","leggings","skirt","skirts","capris"}
            outer_aliases = {"jacket","jackets","coat","coats","blazer","blazers","hoodie","hoodies","cardigan","cardigans","dupatta","dupattas","puffer_jacket","puffer"}
            if cat in tops_aliases:
                # keep only *_tops
                recommender.web_data = {k:v for k,v in recommender.web_data.items() if k.endswith("_men") or k.endswith("_women") or True}
            # We will filter later in _get_available_products by key prefix; here we pass through
        return recommender.generate_shopping_recommendations(season)
    except Exception as e:
        logger.error(f"Error in dynamic shopping recommendations: {e}")
        error_msg = f"❌ Error generating recommendations: {str(e)}"
        return error_msg, error_msg, error_msg, [], []

if __name__ == "__main__":
    # Test the dynamic recommender
    recommender = DynamicShoppingRecommender("clothing_images_men")
    summary, gaps, shopping = recommender.generate_shopping_recommendations("summer")
    print("WARDROBE SUMMARY:")
    print(summary)
    print("\nGAP ANALYSIS:")
    print(gaps)
    print("\nSHOPPING LIST:")
    print(shopping)
