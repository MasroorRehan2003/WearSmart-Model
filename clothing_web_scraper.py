"""
Dynamic Clothing Web Scraper for Pakistani Fashion Websites
Fetches real product data from multiple clothing websites
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClothingWebScraper:
    """Scrapes clothing data from Pakistani fashion websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_data = {}
        
    def scrape_outfitters_men_shirts(self) -> List[Dict]:
        """Scrape men's shirts from Outfitters"""
        try:
            url = "https://outfitters.com.pk/collections/men-shirts"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Debug: Print page structure
            logger.info(f"Page title: {soup.title.string if soup.title else 'No title'}")
            
            # Try multiple selectors for product containers
            selectors = [
                'div[class*="product"]',
                'div[class*="item"]', 
                'div[class*="card"]',
                'article',
                '.product-item',
                '.product-card',
                '.grid-item'
            ]
            
            product_containers = []
            for selector in selectors:
                containers = soup.select(selector)
                if containers:
                    logger.info(f"Found {len(containers)} containers with selector: {selector}")
                    product_containers.extend(containers)
                    break
            
            if not product_containers:
                # Fallback: look for any div with product-related classes
                product_containers = soup.find_all('div', class_=lambda x: x and any(word in x.lower() for word in ['product', 'item', 'card', 'grid']))
                logger.info(f"Fallback found {len(product_containers)} containers")
            
            # If still no containers, try to find any links that might be products
            if not product_containers:
                product_links = soup.find_all('a', href=re.compile(r'/products/'))
                logger.info(f"Found {len(product_links)} product links")
                for link in product_links[:10]:  # Limit to first 10
                    parent = link.parent
                    if parent:
                        product_containers.append(parent)
            
            logger.info(f"Processing {len(product_containers)} product containers")
            
            for i, container in enumerate(product_containers[:20]):  # Limit to first 20
                try:
                    # Extract product name - try multiple approaches
                    name = ""
                    name_selectors = ['h3', 'h4', 'h5', 'h2', '.title', '.name', '.product-title', 'a[href*="/products/"]']
                    
                    for selector in name_selectors:
                        name_elem = container.select_one(selector)
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                            if name and len(name) > 3:  # Valid name
                                break
                    
                    if not name:
                        # Try getting text from any link
                        link = container.find('a', href=re.compile(r'/products/'))
                        if link:
                            name = link.get_text(strip=True)
                    
                    if not name or len(name) < 3:
                        continue
                    
                    # Extract price
                    price = "Price not available"
                    price_selectors = ['.price', '.cost', '[class*="price"]', 'span:contains("PKR")', 'div:contains("PKR")']
                    
                    for selector in price_selectors:
                        price_elem = container.select_one(selector)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price_match = re.search(r'PKR\s*([\d,]+)', price_text)
                            if price_match:
                                price = f"PKR {price_match.group(1)}"
                                break
                    
                    # Extract colors - look for color swatches or color names
                    colors = []
                    color_selectors = ['.color', '.swatch', '[class*="color"]', '[class*="swatch"]']
                    
                    for selector in color_selectors:
                        color_elements = container.select(selector)
                        for color_elem in color_elements:
                            color_text = color_elem.get_text(strip=True)
                            if color_text and len(color_text) < 30 and color_text not in colors:
                                colors.append(color_text)
                    
                    # If no colors found, try to extract from product name
                    if not colors:
                        color_keywords = ['black', 'white', 'blue', 'red', 'green', 'brown', 'grey', 'gray', 'navy', 'beige', 'ivory', 'off-white']
                        for keyword in color_keywords:
                            if keyword in name.lower():
                                colors.append(keyword.title())
                    
                    # Extract image URL
                    image_url = ""
                    img_elem = container.find('img')
                    if img_elem:
                        img_src = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy')
                        if img_src:
                            if img_src.startswith('//'):
                                image_url = 'https:' + img_src
                            elif img_src.startswith('/'):
                                image_url = 'https://outfitters.com.pk' + img_src
                            else:
                                image_url = urljoin(url, img_src)
                    
                    # Extract product URL
                    product_url = ""
                    link_elem = container.find('a', href=True)
                    if link_elem:
                        href = link_elem['href']
                        if href.startswith('/'):
                            product_url = 'https://outfitters.com.pk' + href
                        elif href.startswith('http'):
                            product_url = href
                        else:
                            product_url = urljoin(url, href)
                    
                    # Only add if we have a valid name
                    if name and len(name) > 3:
                        product = {
                            'name': name,
                            'price': price,
                            'colors': colors[:5],  # Limit to 5 colors
                            'image_url': image_url,
                            'product_url': product_url,
                            'website': 'Outfitters',
                            'category': 'shirts',
                            'gender': 'men'
                        }
                        products.append(product)
                        logger.info(f"Added product {i+1}: {name}")
                        
                except Exception as e:
                    logger.warning(f"Error parsing product container {i+1}: {e}")
                    continue
            
            logger.info(f"Scraped {len(products)} men's shirts from Outfitters")
            return products
            
        except Exception as e:
            logger.error(f"Error scraping Outfitters men's shirts: {e}")
            return []
    
    def _scrape_outfitters_collection(self, url: str, category: str, gender: str) -> List[Dict]:
        """Generic scraper for an Outfitters collection URL."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            products: List[Dict] = []
            selectors = [
                'div[class*="product"]','div[class*="item"]','div[class*="card"]','article',
                '.product-item','.product-card','.grid-item'
            ]
            containers: List = []
            for sel in selectors:
                tmp = soup.select(sel)
                if tmp:
                    containers.extend(tmp)
                    break
            if not containers:
                containers = soup.find_all('div', class_=lambda x: x and any(w in x.lower() for w in ['product','item','card','grid']))
            if not containers:
                links = soup.find_all('a', href=re.compile(r'/products/'))
                for lk in links[:20]:
                    if lk.parent:
                        containers.append(lk.parent)
            seen = set()
            for container in containers[:60]:
                try:
                    # name
                    name = ""
                    for sel in ['h3','h4','h5','h2','.title','.name','.product-title','a[href*="/products/"]']:
                        el = container.select_one(sel)
                        if el:
                            t = el.get_text(strip=True)
                            if t and len(t) > 3:
                                name = t
                                break
                    if not name:
                        lk = container.find('a', href=re.compile(r'/products/'))
                        if lk:
                            name = lk.get_text(strip=True)
                    if not name or len(name) < 3:
                        continue
                    # price
                    price = "Price not available"
                    for sel in ['.price','.cost','[class*="price"]']:
                        el = container.select_one(sel)
                        if el:
                            txt = el.get_text(strip=True)
                            m = re.search(r'PKR\s*([\d,]+)', txt)
                            if m:
                                price = f"PKR {m.group(1)}"
                                break
                    # colors
                    colors: List[str] = []
                    for sel in ['.color','.swatch','[class*="color"]','[class*="swatch"]']:
                        for ce in container.select(sel):
                            ct = (ce.get_text(strip=True) or '').strip()
                            if not ct:
                                continue
                            tl = ct.lower()
                            if tl in {"xs","s","m","l","xl","xxl","xxxl","one size"}:
                                continue
                            if "fit" in tl or "women" in tl or "men" in tl or re.search(r"\b\d+\s*colors?\b", tl):
                                continue
                            if len(ct) < 50 and ct not in colors:
                                colors.append(ct)
                    # image
                    image_url = ""
                    img = container.find('img')
                    if img:
                        src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                        if src:
                            if src.startswith('//'):
                                image_url = 'https:' + src
                            elif src.startswith('/'):
                                image_url = 'https://outfitters.com.pk' + src
                            else:
                                image_url = urljoin(url, src)
                    # product link
                    prod_url = ""
                    pl = container.find('a', href=re.compile(r'/products/'))
                    if pl and pl.get('href'):
                        href = pl['href']
                    else:
                        anyl = container.find('a', href=True)
                        href = anyl['href'] if anyl else ''
                    if href:
                        if href.startswith('/'):
                            prod_url = 'https://outfitters.com.pk' + href
                        elif href.startswith('http'):
                            prod_url = href
                        else:
                            prod_url = urljoin(url, href)
                    key = prod_url or (name + image_url)
                    if key in seen:
                        continue
                    seen.add(key)
                    products.append({
                        'name': name,
                        'price': price,
                        'colors': colors[:5],
                        'image_url': image_url,
                        'product_url': prod_url,
                        'website': 'Outfitters',
                        'category': category.lower(),
                        'gender': gender.lower()
                    })
                except Exception:
                    continue
            return products
        except Exception as e:
            logger.error(f"Error scraping Outfitters collection {url}: {e}")
            return []

    def ensure_outfitters_category(self, gender: str, category: str) -> List[Dict]:
        """Ensure we have products for a specific Outfitters collection by gender/category."""
        gender_l = (gender or 'men').lower()
        cat_l = (category or '').strip().lower()
        base = 'https://outfitters.com.pk/collections/'
        # Map common categories to Outfitters slugs
        men_map = {
            'shirt': 'men-shirts', 'shirts': 'men-shirts', 't-shirt': 'men-t-shirts', 'tshirts': 'men-t-shirts',
            'jeans': 'men-jeans', 'trousers': 'men-trousers', 'shorts': 'men-shorts', 'outerwear': 'men-outerwear',
            'sweater': 'men-sweaters', 'hoodie': 'men-hoodies'
        }
        women_map = {
            'shirt': 'women-shirts', 'shirts': 'women-shirts', 't-shirt': 'women-t-shirts', 'tshirts': 'women-t-shirts',
            'jeans': 'women-jeans', 'trousers': 'women-trousers', 'shorts': 'women-shorts', 'outerwear': 'women-outerwear',
            'sweater': 'women-sweaters', 'hoodie': 'women-hoodies', 'dresses': 'women-dresses-jumpsuits'
        }
        slug = (men_map if gender_l == 'men' else women_map).get(cat_l)
        if not slug:
            return []
        url = base + slug
        products = self._scrape_outfitters_collection(url, category=cat_l, gender=gender_l)
        key = f"outfitters_{gender_l}"
        self.scraped_data.setdefault(key, [])
        # merge unique by product_url
        existing_urls = {p.get('product_url') for p in self.scraped_data[key]}
        for p in products:
            if p.get('product_url') not in existing_urls:
                self.scraped_data[key].append(p)
        return products
    def scrape_outfitters_women_shirts(self) -> List[Dict]:
        """Scrape women's shirts from Outfitters (robust selectors)"""
        try:
            url = "https://outfitters.com.pk/collections/women-shirts"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products: List[Dict] = []
            
            logger.info(f"[Women] Page title: {soup.title.string if soup.title else 'No title'}")
            selectors = [
                'div[class*="product"]',
                'div[class*="item"]',
                'div[class*="card"]',
                'article',
                '.product-item',
                '.product-card',
                '.grid-item'
            ]
            product_containers: List = []
            for sel in selectors:
                found = soup.select(sel)
                if found:
                    logger.info(f"[Women] Found {len(found)} containers with selector: {sel}")
                    product_containers.extend(found)
                    break
            if not product_containers:
                product_containers = soup.find_all('div', class_=lambda x: x and any(w in x.lower() for w in ['product','item','card','grid']))
                logger.info(f"[Women] Fallback found {len(product_containers)} containers")
            if not product_containers:
                product_links = soup.find_all('a', href=re.compile(r'/products/'))
                logger.info(f"[Women] Found {len(product_links)} product links")
                for link in product_links[:10]:
                    if link.parent:
                        product_containers.append(link.parent)
            
            logger.info(f"[Women] Processing {len(product_containers)} product containers")
            for i, container in enumerate(product_containers[:20]):
                try:
                    # Name
                    name = ""
                    for sel in ['h3','h4','h5','h2','.title','.name','.product-title','a[href*="/products/"]']:
                        el = container.select_one(sel)
                        if el:
                            t = el.get_text(strip=True)
                            if t and len(t) > 3:
                                name = t
                                break
                    if not name:
                        link = container.find('a', href=re.compile(r'/products/'))
                        if link:
                            name = link.get_text(strip=True)
                    if not name or len(name) < 3:
                        continue
                    
                    # Price
                    price = "Price not available"
                    for sel in ['.price','.cost','[class*="price"]']:
                        el = container.select_one(sel)
                        if el:
                            txt = el.get_text(strip=True)
                            m = re.search(r'PKR\s*([\d,]+)', txt)
                            if m:
                                price = f"PKR {m.group(1)}"
                                break
                    
                    # Colors
                    colors: List[str] = []
                    for sel in ['.color','.swatch','[class*="color"]','[class*="swatch"]']:
                        for ce in container.select(sel):
                            ct = ce.get_text(strip=True)
                            if ct and len(ct) < 50 and ct not in colors:
                                colors.append(ct)
                    if not colors:
                        for kw in ['black','white','blue','red','green','brown','grey','gray','navy','beige','ivory','off-white']:
                            if kw in name.lower():
                                colors.append(kw.title())
                    
                    # Image URL
                    image_url = ""
                    img = container.find('img')
                    if img:
                        src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                        if src:
                            if src.startswith('//'):
                                image_url = 'https:' + src
                            elif src.startswith('/'):
                                image_url = 'https://outfitters.com.pk' + src
                            else:
                                image_url = urljoin(url, src)
                    
                    # Product URL (prefer /products/)
                    product_url = ""
                    prod_link = container.find('a', href=re.compile(r'/products/'))
                    if prod_link and prod_link.get('href'):
                        href = prod_link['href']
                    else:
                        any_link = container.find('a', href=True)
                        href = any_link['href'] if any_link else ''
                    if href:
                        if href.startswith('/'):
                            product_url = 'https://outfitters.com.pk' + href
                        elif href.startswith('http'):
                            product_url = href
                        else:
                            product_url = urljoin(url, href)
                    
                    prod = {
                        'name': name,
                        'price': price,
                        'colors': colors[:5],
                        'image_url': image_url,
                        'product_url': product_url,
                        'website': 'Outfitters',
                        'category': 'shirts',
                        'gender': 'women'
                    }
                    products.append(prod)
                except Exception as e:
                    logger.warning(f"[Women] Error parsing container {i+1}: {e}")
                    continue
            
            logger.info(f"Scraped {len(products)} women's shirts from Outfitters")
            return products
        
        except Exception as e:
            logger.error(f"Error scraping Outfitters women's shirts: {e}")
            return []
    
    def scrape_khaadi_men(self) -> List[Dict]:
        """Scrape men's clothing from Khaadi"""
        try:
            # Khaadi men's clothing URL (adjust as needed)
            url = "https://khaadi.com/men"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Similar scraping logic for Khaadi
            product_containers = soup.find_all('div', class_=re.compile(r'product|item|card'))
            
            for container in product_containers:
                try:
                    name_elem = container.find(['h3', 'h4', 'h5'], class_=re.compile(r'title|name|product'))
                    if not name_elem:
                        continue
                    name = name_elem.get_text(strip=True)
                    
                    price_elem = container.find(['span', 'div'], class_=re.compile(r'price|cost'))
                    price = "Price not available"
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        price_match = re.search(r'PKR\s*([\d,]+)', price_text)
                        if price_match:
                            price = f"PKR {price_match.group(1)}"
                    
                    colors = []
                    color_elements = container.find_all(['span', 'div'], class_=re.compile(r'color|swatch'))
                    for color_elem in color_elements:
                        color_text = color_elem.get_text(strip=True)
                        if color_text and len(color_text) < 20:
                            colors.append(color_text)
                    
                    img_elem = container.find('img')
                    image_url = ""
                    if img_elem:
                        img_src = img_elem.get('src') or img_elem.get('data-src')
                        if img_src:
                            image_url = urljoin(url, img_src)
                    
                    link_elem = container.find('a', href=True)
                    product_url = ""
                    if link_elem:
                        product_url = urljoin(url, link_elem['href'])
                    
                    if name and name != "":
                        products.append({
                            'name': name,
                            'price': price,
                            'colors': colors,
                            'image_url': image_url,
                            'product_url': product_url,
                            'website': 'Khaadi',
                            'category': 'general',
                            'gender': 'men'
                        })
                        
                except Exception as e:
                    logger.warning(f"Error parsing Khaadi product container: {e}")
                    continue
            
            logger.info(f"Scraped {len(products)} men's items from Khaadi")
            return products
            
        except Exception as e:
            logger.error(f"Error scraping Khaadi men's clothing: {e}")
            return []
    
    def scrape_all_websites(self) -> Dict[str, List[Dict]]:
        """Scrape all configured websites"""
        all_products = {
            'outfitters_men': [],
            'outfitters_women': [],
            'khaadi_men': []
        }
        
        logger.info("Starting web scraping from Pakistani clothing websites...")
        
        # Scrape Outfitters men's shirts
        logger.info("Scraping Outfitters men's shirts...")
        all_products['outfitters_men'] = self.scrape_outfitters_men_shirts()
        time.sleep(2)  # Be respectful to the website
        
        # Scrape Outfitters women's shirts
        logger.info("Scraping Outfitters women's shirts...")
        all_products['outfitters_women'] = self.scrape_outfitters_women_shirts()
        time.sleep(2)
        
        # Scrape Khaadi men's clothing
        logger.info("Scraping Khaadi men's clothing...")
        all_products['khaadi_men'] = self.scrape_khaadi_men()
        
        self.scraped_data = all_products
        return all_products
    
    def save_to_json(self, filename: str = "scraped_clothing_data.json"):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Scraped data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving data to JSON: {e}")
    
    def load_from_json(self, filename: str = "scraped_clothing_data.json") -> Dict:
        """Load previously scraped data from JSON file"""
        try:
            if Path(filename).exists():
                with open(filename, 'r', encoding='utf-8') as f:
                    self.scraped_data = json.load(f)
                logger.info(f"Loaded data from {filename}")
                return self.scraped_data
            else:
                logger.warning(f"File {filename} not found")
                return {}
        except Exception as e:
            logger.error(f"Error loading data from JSON: {e}")
            return {}
    
    def get_products_by_color(self, color: str, gender: str = "men") -> List[Dict]:
        """Get products filtered by color and gender"""
        if not self.scraped_data:
            self.load_from_json()
        
        matching_products = []
        color_lower = color.lower()
        
        for website, products in self.scraped_data.items():
            if gender not in website:
                continue
                
            for product in products:
                # Check if color matches in product colors
                product_colors = [c.lower() for c in product.get('colors', [])]
                if any(color_lower in pc for pc in product_colors):
                    matching_products.append(product)
                # Also check product name for color mentions
                elif color_lower in product.get('name', '').lower():
                    matching_products.append(product)
        
        return matching_products
    
    def get_products_by_category(self, category: str, gender: str = "men") -> List[Dict]:
        """Get products filtered by category and gender"""
        if not self.scraped_data:
            self.load_from_json()
        
        matching_products = []
        category_lower = category.lower()
        
        for website, products in self.scraped_data.items():
            if gender not in website:
                continue
                
            for product in products:
                if category_lower in product.get('category', '').lower():
                    matching_products.append(product)
        
        return matching_products

def main():
    """Test the scraper"""
    scraper = ClothingWebScraper()
    
    # Scrape all websites
    all_data = scraper.scrape_all_websites()
    
    # Save to JSON
    scraper.save_to_json()
    
    # Test color filtering
    blue_products = scraper.get_products_by_color("blue", "men")
    print(f"Found {len(blue_products)} blue men's products")
    
    # Test category filtering
    shirt_products = scraper.get_products_by_category("shirts", "men")
    print(f"Found {len(shirt_products)} men's shirts")

if __name__ == "__main__":
    main()
