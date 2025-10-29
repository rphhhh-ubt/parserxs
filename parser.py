import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def search_product(query: str) -> list[dict]:
    """
    Search for products on Lenta.com in alcohol/drinks category.
    
    Args:
        query: Search query string
        
    Returns:
        List of products with id, name, and volume. Empty list if nothing found.
        Example: [{"id": "123456", "name": "Product Name", "volume": "0.5 л"}]
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
            page.set_default_timeout(30000)
            
            print("[search_product] Navigating to lenta.com...")
            await page.goto("https://lenta.com", wait_until="domcontentloaded", timeout=30000)
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Try to select Moscow region
            try:
                print("[search_product] Attempting to select Moscow region...")
                # Look for region selector button
                region_button = page.locator("button:has-text('Москва'), a:has-text('Москва'), [data-testid*='city'], [class*='city'], [class*='region']").first
                await region_button.wait_for(state="visible", timeout=10000)
                await region_button.click()
                await asyncio.sleep(1)
                
                # Try to click on Moscow option
                moscow_option = page.locator("text=/Москва/i").first
                await moscow_option.click(timeout=5000)
                await asyncio.sleep(1)
                print("[search_product] Moscow region selected")
            except Exception as e:
                print(f"[search_product] Could not select region (may already be selected): {e}")
            
            # Navigate to alcohol/drinks category
            try:
                print("[search_product] Navigating to alcohol category...")
                # Try different possible URLs for alcohol category
                alcohol_urls = [
                    "https://lenta.com/catalog/alkogol/",
                    "https://lenta.com/catalog/alkogolnye-napitki/",
                    "https://lenta.com/catalog/napitki/alkogol/"
                ]
                
                for url in alcohol_urls:
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                        await asyncio.sleep(2)
                        break
                    except:
                        continue
                        
                print("[search_product] Alcohol category page loaded")
            except Exception as e:
                print(f"[search_product] Could not navigate to alcohol category: {e}")
            
            # Perform search
            print(f"[search_product] Searching for '{query}'...")
            try:
                # Look for search input field
                search_input = page.locator("input[type='search'], input[placeholder*='поиск' i], input[name='q'], input[name='search']").first
                await search_input.wait_for(state="visible", timeout=10000)
                await search_input.fill(query)
                await asyncio.sleep(1)
                
                # Submit search
                await search_input.press("Enter")
                await asyncio.sleep(3)
                print("[search_product] Search submitted")
            except Exception as e:
                print(f"[search_product] Error performing search: {e}")
                await browser.close()
                return []
            
            # Parse search results
            print("[search_product] Parsing search results...")
            products = []
            
            try:
                # Wait for product cards to appear
                await page.wait_for_selector("[data-testid*='product'], [class*='product-card'], .product, article", timeout=10000)
                await asyncio.sleep(2)
                
                # Get all product cards
                product_cards = page.locator("[data-testid*='product'], [class*='product-card'], .product, article")
                count = await product_cards.count()
                print(f"[search_product] Found {count} product cards")
                
                for i in range(min(count, 20)):  # Limit to first 20 products
                    try:
                        card = product_cards.nth(i)
                        
                        # Extract product ID from data attribute or URL
                        product_id = None
                        try:
                            product_id = await card.get_attribute("data-id")
                            if not product_id:
                                product_id = await card.get_attribute("data-product-id")
                            if not product_id:
                                # Try to get ID from link href
                                link = card.locator("a[href*='/product/']").first
                                href = await link.get_attribute("href")
                                if href:
                                    # Extract ID from URL like /product/123456/
                                    parts = href.split("/")
                                    for part in parts:
                                        if part.isdigit():
                                            product_id = part
                                            break
                        except:
                            pass
                        
                        # Extract product name
                        name = None
                        try:
                            name_elem = card.locator("h2, h3, h4, [class*='title'], [class*='name'], [data-testid*='name']").first
                            name = await name_elem.text_content()
                            name = name.strip() if name else None
                        except:
                            pass
                        
                        # Extract volume
                        volume = None
                        try:
                            # Look for volume in text like "0.5 л", "500 мл", etc.
                            card_text = await card.text_content()
                            import re
                            volume_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(л|мл|ml|l)\b', card_text, re.IGNORECASE)
                            if volume_match:
                                volume = volume_match.group(0)
                        except:
                            pass
                        
                        # Only add if we have at least product_id and name
                        if product_id and name:
                            product = {
                                "id": product_id,
                                "name": name,
                                "volume": volume or ""
                            }
                            products.append(product)
                            print(f"[search_product] Found: {product}")
                    except Exception as e:
                        print(f"[search_product] Error parsing product card {i}: {e}")
                        continue
                
            except Exception as e:
                print(f"[search_product] Error parsing results: {e}")
            
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
        product_id: Product ID from Lenta.com
        
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
                f"https://lenta.com/catalog/product/{product_id}/",
                f"https://lenta.com/product/{product_id}"
            ]
            
            print("[get_prices_by_stores] Navigating to product page...")
            page_loaded = False
            for url in product_urls:
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(3)
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
                
                # Look for store selector button/dropdown
                store_selector = page.locator(
                    "button:has-text('Магазин'), "
                    "button:has-text('магазин'), "
                    "[data-testid*='store'], "
                    "[class*='store-selector'], "
                    "[class*='shop-selector']"
                ).first
                
                await store_selector.wait_for(state="visible", timeout=10000)
                await store_selector.click()
                await asyncio.sleep(2)
                print("[get_prices_by_stores] Store selector opened")
                
                # Get list of stores
                store_items = page.locator(
                    "[data-testid*='store-item'], "
                    "[class*='store-item'], "
                    "[class*='shop-item'], "
                    "li:has-text('ТК'), "
                    "div:has-text('ТК')"
                )
                
                store_count = await store_items.count()
                print(f"[get_prices_by_stores] Found {store_count} stores")
                
                # Limit to first 30 stores
                for i in range(min(store_count, 30)):
                    try:
                        store_item = store_items.nth(i)
                        
                        # Click on store to select it
                        await store_item.click()
                        await asyncio.sleep(1.5)
                        
                        # Extract store information
                        store_text = await store_item.text_content()
                        store_text = store_text.strip() if store_text else ""
                        
                        # Parse store name and address
                        import re
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
                                address = address_part[1].strip()
                        else:
                            # If no store code found, use first part as name
                            parts = store_text.split(",", 1)
                            store_name = parts[0].strip() if parts else store_text
                            address = parts[1].strip() if len(parts) > 1 else ""
                        
                        # Extract price for this store
                        price = None
                        try:
                            # Look for price element
                            price_elem = page.locator(
                                "[class*='price'], "
                                "[data-testid*='price'], "
                                "span:has-text('₽'), "
                                "[itemprop='price']"
                            ).first
                            
                            await price_elem.wait_for(state="visible", timeout=5000)
                            price_text = await price_elem.text_content()
                            
                            # Parse price from text like "599 ₽" or "599.99"
                            price_match = re.search(r'(\d+(?:[.,]\d{1,2})?)', price_text.replace(" ", ""))
                            if price_match:
                                price_str = price_match.group(1).replace(",", ".")
                                price = float(price_str)
                        except Exception as e:
                            print(f"[get_prices_by_stores] Could not get price for store {i}: {e}")
                        
                        # Check if product is in stock
                        in_stock = True
                        try:
                            out_of_stock_elem = page.locator("text=/нет в наличии/i, text=/out of stock/i").first
                            if await out_of_stock_elem.count() > 0:
                                in_stock = False
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
                            await store_selector.click()
                            await asyncio.sleep(1)
                            
                    except Exception as e:
                        print(f"[get_prices_by_stores] Error processing store {i}: {e}")
                        continue
                
            except Exception as e:
                print(f"[get_prices_by_stores] Error with store selector: {e}")
                # Try alternative: get all prices from page without clicking
                try:
                    print("[get_prices_by_stores] Trying alternative method...")
                    
                    # Look for store list container
                    store_list = page.locator("[class*='store-list'], [class*='shop-list']")
                    all_text = await page.text_content("body")
                    
                    # Parse all store info from page text
                    import re
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
