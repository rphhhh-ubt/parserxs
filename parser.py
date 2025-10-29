import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def search_product(query: str) -> list[dict]:
    """
    Search for products on Lenta.com in alcohol/drinks category.
    
    Args:
        query: Search query string
        
    Returns:
        List of products with id, name, volume, and price. Empty list if nothing found.
        Example: [{"id": "123456", "name": "Product Name", "volume": "0.5 л", "price": "599.00"}]
    """
    print(f"[search_product] Starting search for: {query}")
    
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="ru-RU",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            page.set_default_timeout(15000)
            
            print("[search_product] Navigating to https://lenta.com")
            await page.goto("https://lenta.com", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(3)

            print("[search_product] Looking for search input...")
            search_input = await page.wait_for_selector('#header-search-input', timeout=15000)
            
            print(f"[search_product] Filling search input with: {query}")
            await search_input.fill(query)
            await search_input.press('Enter')
            
            await asyncio.sleep(3)
            
            print("[search_product] Waiting for product cards...")
            await page.wait_for_selector('a.product-card', timeout=15000)
            
            cards = await page.query_selector_all('a.product-card')
            print(f"[search_product] Found {len(cards)} product cards.")
            
            products = []
            for i, card in enumerate(cards[:10]):  # Limit to first 10 products
                try:
                    href = await card.get_attribute('href')
                    if not href:
                        continue
                        
                    product_id = href.split('-')[-1].replace('/', '')
                    
                    name_element = await card.query_selector('.card-name_content')
                    name = await name_element.inner_text() if name_element else "Unknown"
                    
                    price_element = await card.query_selector('.main-price')
                    price = await price_element.inner_text() if price_element else "N/A"

                    product = {
                        "id": product_id,
                        "name": name.strip(),
                        "volume": "",
                        "price": price.strip()
                    }
                    products.append(product)
                    print(f"[search_product] Parsed product {i+1}: {product}")

                except Exception as e:
                    print(f"[search_product] Error parsing product card {i}: {e}")
                    continue
            
            await browser.close()
            print(f"[search_product] Search completed. Found {len(products)} products")
            return products
            
    except PlaywrightTimeoutError as e:
        print(f"[search_product] Timeout error: {e}")
        if browser:
            await browser.close()
        return []
    except Exception as e:
        print(f"[search_product] Error: {e}")
        if browser:
            await browser.close()
        return []


async def get_prices_by_stores(product_id: str) -> list[dict]:
    """
    Get prices for a product across different Lenta stores in Moscow.
    
    Args:
        product_id: Product ID from Lenta.com (can be slug like "product-name-123456")
        
    Returns:
        List of stores with prices. Empty list if no stores found.
        Example: [{"store": "ТК124", "address": "7-я Кожуховская 9", "price": 599.00}]
    """
    print(f"[get_prices_by_stores] Getting prices for product ID: {product_id}")
    
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="ru-RU",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            page.set_default_timeout(30000)
            
            # Try different possible product URL formats
            product_urls = [
                f"https://lenta.com/product/{product_id}/",
                f"https://lenta.com/product/{product_id}",
                f"https://lenta.com/catalog/product/{product_id}/"
            ]
            
            print("[get_prices_by_stores] Navigating to product page...")
            page_loaded = False
            for url in product_urls:
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Wait for network to be idle
                    try:
                        await page.wait_for_load_state("networkidle", timeout=30000)
                    except Exception as e:
                        print(f"[get_prices_by_stores] Warning: networkidle timeout: {e}")
                    
                    await asyncio.sleep(2)
                    page_loaded = True
                    print(f"[get_prices_by_stores] Loaded: {url}")
                    break
                except Exception as e:
                    print(f"[get_prices_by_stores] Failed to load {url}: {e}")
                    continue
            
            if not page_loaded:
                print("[get_prices_by_stores] Could not load product page")
                await browser.close()
                return []
            
            stores_data = []
            
            # Try to find and click store selector
            try:
                print("[get_prices_by_stores] Looking for store selector...")
                
                # Try multiple selectors for store selector button
                store_selector_selectors = [
                    "button:has-text('Выбрать магазин')",
                    "button:has-text('магазин')",
                    "button:has-text('Магазин')",
                    "[data-testid*='store-selector']",
                    "[data-testid*='shop-selector']",
                    "[class*='store-selector']",
                    "[class*='shop-selector']",
                    "button[class*='store']",
                    "button[class*='shop']"
                ]
                
                store_selector = None
                successful_selector = None
                
                for selector in store_selector_selectors:
                    try:
                        print(f"[get_prices_by_stores] Trying store selector: {selector}")
                        temp_selector = page.locator(selector).first
                        await temp_selector.wait_for(state="visible", timeout=30000)
                        store_selector = temp_selector
                        successful_selector = selector
                        print(f"[get_prices_by_stores] Found store selector with: {selector}")
                        break
                    except Exception as e:
                        print(f"[get_prices_by_stores] Store selector '{selector}' not found: {e}")
                        continue
                
                if not store_selector:
                    raise Exception("No store selector found with any selector")
                
                await store_selector.click()
                await asyncio.sleep(2)
                print("[get_prices_by_stores] Store selector opened")
                
                # Get list of stores - try multiple selectors
                store_item_selectors = [
                    "[data-testid*='store-item']",
                    "[class*='store-item']",
                    "[class*='shop-item']",
                    "li:has-text('ТК')",
                    "div:has-text('ТК')",
                    "[role='option']",
                    "li[class*='item']"
                ]
                
                store_items = None
                for selector in store_item_selectors:
                    try:
                        print(f"[get_prices_by_stores] Trying store items selector: {selector}")
                        temp_items = page.locator(selector)
                        count = await temp_items.count()
                        if count > 0:
                            store_items = temp_items
                            print(f"[get_prices_by_stores] Found {count} stores with selector: {selector}")
                            break
                    except:
                        continue
                
                if not store_items:
                    raise Exception("No store items found with any selector")
                
                store_count = await store_items.count()
                
                # Limit to first 30 stores
                for i in range(min(store_count, 30)):
                    try:
                        store_item = store_items.nth(i)
                        
                        # Extract store information before clicking
                        store_text = await store_item.text_content()
                        store_text = store_text.strip() if store_text else ""
                        
                        # Parse store name and address
                        store_name = ""
                        address = ""
                        
                        # Try to extract store code like "ТК124"
                        store_match = re.search(r'ТК\s*\d+', store_text)
                        if store_match:
                            store_name = store_match.group(0).replace(" ", "")
                        
                        # Try to extract address (everything after store code)
                        if store_name:
                            address_part = store_text.split(store_name, 1)
                            if len(address_part) > 1:
                                address = address_part[1].strip().strip(",").strip()
                        else:
                            # If no store code found, use first part as name
                            parts = store_text.split(",", 1)
                            store_name = parts[0].strip() if parts else store_text
                            address = parts[1].strip() if len(parts) > 1 else ""
                        
                        # Click on store to select it
                        await store_item.click()
                        await asyncio.sleep(2)
                        
                        # Wait for price to update
                        await asyncio.sleep(1)
                        
                        # Extract price for this store
                        price = None
                        price_selectors = [
                            "[class*='price']",
                            "[data-testid*='price']",
                            ".product-price",
                            "span:has-text('₽')",
                            "[itemprop='price']"
                        ]
                        
                        for price_sel in price_selectors:
                            try:
                                price_elem = page.locator(price_sel).first
                                await price_elem.wait_for(state="visible", timeout=5000)
                                price_text = await price_elem.text_content()
                                
                                # Parse price from text like "599 ₽" or "599.99"
                                price_match = re.search(r'(\d+(?:[.,]\d{1,2})?)', price_text.replace(" ", "").replace("\xa0", ""))
                                if price_match:
                                    price_str = price_match.group(1).replace(",", ".")
                                    price = float(price_str)
                                    break
                            except:
                                continue
                        
                        if not price:
                            print(f"[get_prices_by_stores] Could not get price for store {i}")
                        
                        # Check if product is in stock
                        in_stock = True
                        try:
                            out_of_stock_indicators = [
                                "text=/нет в наличии/i",
                                "text=/out of stock/i",
                                "text=/недоступен/i",
                                "[data-testid*='out-of-stock']"
                            ]
                            for indicator in out_of_stock_indicators:
                                out_of_stock_elem = page.locator(indicator).first
                                count = await out_of_stock_elem.count()
                                if count > 0:
                                    in_stock = False
                                    break
                        except:
                            pass
                        
                        # Only add store if it has a price and is in stock
                        if price and in_stock and store_name:
                            store_data = {
                                "store": store_name,
                                "address": address,
                                "price": price
                            }
                            stores_data.append(store_data)
                            print(f"[get_prices_by_stores] Store {i}: {store_data}")
                        else:
                            print(f"[get_prices_by_stores] Skipping store {i} (no price or out of stock)")
                        
                        # Reopen store selector for next iteration
                        if i < min(store_count, 30) - 1:
                            try:
                                await store_selector.click()
                                await asyncio.sleep(1.5)
                            except:
                                print(f"[get_prices_by_stores] Could not reopen store selector")
                                break
                            
                    except Exception as e:
                        print(f"[get_prices_by_stores] Error processing store {i}: {e}")
                        continue
                
            except Exception as e:
                print(f"[get_prices_by_stores] Error with store selector: {e}")
                # Try alternative: get all prices from page without clicking
                try:
                    print("[get_prices_by_stores] Trying alternative method...")
                    
                    # Look for store list container
                    all_text = await page.text_content("body")
                    
                    # Parse all store info from page text
                    store_matches = re.findall(r'(ТК\d+)[^\d]+([\w\s\d,.-]+?)(?:\s+)?(\d+(?:\.\d{2})?)\s*₽', all_text)
                    
                    for match in store_matches[:30]:  # Limit to 30
                        store_name = match[0]
                        address = match[1].strip()
                        price = float(match[2])
                        
                        store_data = {
                            "store": store_name,
                            "address": address,
                            "price": price
                        }
                        stores_data.append(store_data)
                        print(f"[get_prices_by_stores] Alternative parse: {store_data}")
                        
                except Exception as e2:
                    print(f"[get_prices_by_stores] Alternative method failed: {e2}")
            
            await browser.close()
            print(f"[get_prices_by_stores] Completed. Found {len(stores_data)} stores with prices")
            return stores_data
            
    except PlaywrightTimeoutError as e:
        print(f"[get_prices_by_stores] Timeout error: {e}")
        if browser:
            await browser.close()
        return []
    except Exception as e:
        print(f"[get_prices_by_stores] Error: {e}")
        if browser:
            await browser.close()
        return []


# Example usage
if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("Testing search_product...")
        print("=" * 60)
        products = await search_product("водка")
        print(f"\nResults: {len(products)} products found")
        for p in products[:3]:
            print(f"  - {p}")
        
        if products:
            print("\n" + "=" * 60)
            print("Testing get_prices_by_stores...")
            print("=" * 60)
            product_id = products[0]["id"]
            stores = await get_prices_by_stores(product_id)
            print(f"\nResults: {len(stores)} stores found")
            for s in stores[:5]:
                print(f"  - {s}")
    
    asyncio.run(test())
