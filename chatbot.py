import asyncio
import sys
from flask import Flask, jsonify, request
from playwright.async_api import async_playwright
from filter_handler import match_filters
import json

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = Flask(__name__)

@app.route('/scrape', methods=['GET', 'POST'])
async def scrape_hotels():
    try:
        if request.method == 'POST':
            user_input = request.json.get('user_input', '')
        else:
            user_input = request.args.get('user_input', '')

        if not user_input:
            return jsonify({'error': 'Bitte geben Sie einen Suchtext ein'}), 400

        hotels = await scrape_booking(user_input)
        return jsonify({'hotels': hotels})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

async def scrape_booking(user_input):
    city = "Berlin"
    start_date = "2025-05-10"
    end_date = "2025-05-15"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = await browser.new_page()
        await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

        url = f"https://www.booking.com/searchresults.de.html?ss={city.replace(' ', '+')}&checkin={start_date}&checkout={end_date}"
        await page.goto(url, timeout=60000, wait_until="networkidle")

        available_filters = await extract_available_filters(page)

        selected_filters_json = match_filters(user_input, available_filters, start_date, end_date)

        # Ausgabe der Antwort von filter_handler in der Konsole
        print(f"🔍 Antwort von filter_handler: {json.dumps(selected_filters_json, indent=2)}")

        city = selected_filters_json.get("city", city)
        start_date = selected_filters_json.get("start_date", start_date)
        end_date = selected_filters_json.get("end_date", end_date)
        selected_filters = selected_filters_json.get("Filter", [])
        adults = selected_filters_json.get("adults", 2)
        children = selected_filters_json.get("children", 0)
        children_ages = selected_filters_json.get("children_ages", [])
        rooms = selected_filters_json.get("rooms", 1)

        # Ausgabe der angewandten Filter in der Konsole
        print(f"📋 Angewandte Filter: {selected_filters}")

        # Construct the URL with the new parameters
        url = (
            f"https://www.booking.com/searchresults.de.html?ss={city.replace(' ', '+')}"
            f"&checkin={start_date}&checkout={end_date}"
            f"&group_adults={adults}&no_rooms={rooms}&group_children={children}"
        )

        for age in children_ages:
            url += f"&age={age}"

        print(f"🔗 Final URL: {url}")
        await page.goto(url, timeout=60000, wait_until="networkidle")

        await apply_selected_filters(page, selected_filters)
        hotels = await extract_hotels(page)

        await browser.close()

        return hotels

async def extract_available_filters(page):
    filters = {}
    filter_divs = await page.query_selector_all('div[data-filters-item]')

    for div in filter_divs:
        try:
            input_element = await div.query_selector('input[type="checkbox"]')
            filter_value = await input_element.get_attribute("value") if input_element else None
            name_element = await div.query_selector('div[data-testid="filters-group-label-content"]')
            filter_name = await name_element.inner_text() if name_element else None

            if filter_value and filter_name:
                filters[filter_name.strip()] = filter_value.strip()
        except Exception:
            continue

    print(f"📌 Verfügbare Filter: {list(filters.keys())}")
    return filters

async def apply_selected_filters(page, selected_filters):
    for filter_value in selected_filters:
        try:
            label = await page.query_selector(f'label[for="{filter_value}"]')
            if label and await label.is_visible():
                await label.click()
                await asyncio.sleep(1)
                continue
            div = await page.query_selector(f'div[data-filters-item*="{filter_value}"]')
            if div and await div.is_visible():
                await div.click()
                await asyncio.sleep(1)
                continue
            input_element = await page.query_selector(f'input[value="{filter_value}"]')
            if input_element:
                await page.evaluate(f'document.querySelector(\'input[value="{filter_value}"]\').click()')
                await asyncio.sleep(1)
        except Exception as e:
            print(f"❌ Fehler beim Aktivieren von {filter_value}: {e}")

async def extract_hotels(page):
    hotels = []
    hotel_elements = await page.query_selector_all('div[data-testid="property-card"]')

    for hotel in hotel_elements:
        name_element = await hotel.query_selector('div[data-testid="title"]')
        name = await name_element.inner_text() if name_element else "Kein Name"

        price_element = await hotel.query_selector('span[data-testid="price-and-discounted-price"]')
        price = await price_element.inner_text() if price_element else "Kein Preis"

        link_element = await hotel.query_selector('h3 a[data-testid="title-link"]')
        link = await link_element.get_attribute('href') if link_element else "Kein Link"

        hotels.append({"name": name.strip(), "price": price.strip(), "link": link})

    print(f"🏨 {len(hotels)} Hotels gefunden!")
    return hotels

if __name__ == '__main__':
    app.run(port=5000)