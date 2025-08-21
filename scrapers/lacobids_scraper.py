import asyncio
import re
import sys
import json

from playwright.async_api import async_playwright

# Path to optionally save results
OUTPUT_FILE = "./laco_latest.json"


async def main():
    qtd = int(os.getenv("SCRAPE_LACO_QTY", "20"))        # <-- from env
    headless = os.getenv("HEADLESS", "True") == "True"
    """
    Scraper for Los Angeles County (LACo) Bids portal.

    Flow:
      1. Launch Playwright Chromium in headless mode.
      2. Navigate to the LACoBids open solicitations page.
      3. Configure table to show up to 100 rows per page.
      4. Wait for the Angular-powered table to render.
      5. For each of the first N rows, extract fields:
         - solicitation_number (displayed ID)
         - bid_id (parsed from JS onclick)
         - title
         - commodity (category/description)
         - type (solicitation type)
         - department (issuing agency)
         - close_date (submission deadline)
      6. Store results in a normalized JSON list and print to stdout.
    """

    async with async_playwright() as p:

        print("[LOGS] Launching Chromium", file=sys.stderr)
        browser = await p.chromium.launch(headless=headless)

        print("[LOGS] Opening a new page", file=sys.stderr)
        page = await browser.new_page()

        # Target: LA County Open Bids page
        link = "https://camisvr.co.la.ca.us/LACoBids/BidLookUp/OpenBidList"
        print(f"[LOGS] Navigating to: {link}", file=sys.stderr)
        await page.goto(link, timeout=60000)

        opportunities = []

        for c in range(qtd):
            # Always force table to display 100 rows for consistency
            await page.select_option("select[ng-model='main.PageSizeSelect']", "100")

            print("[LOGS] Page loaded successfully", file=sys.stderr)

            # Wait for Angular to fully render the rows
            print("[LOGS] Waiting for table to render", file=sys.stderr)
            await page.wait_for_selector("#searchTbl1 tr")
            print("[LOGS] Table found", file=sys.stderr)

            # Grab all rows
            linhas = page.locator("#searchTbl1 > tr")
            total = await linhas.count()

            print(f"[LOGS] Found {total} rows (processing {qtd})", file=sys.stderr)
            print(f"[LOGS] Processing row {c+1}/{qtd}", file=sys.stderr)

            linha = linhas.nth(c)
            colunas = linha.locator("td")

            # --- Field extraction -----------------------------------------------------

            # 1) Solicitation number + bid_id (parsed from onclick link)
            link_detalhes = colunas.nth(0).locator("a[data-content='Select solicitation']")
            href_value = await link_detalhes.get_attribute("href")
            m = re.search(r"selectBid\('(\d+)'\)", href_value or "")
            bid_id = m.group(1) if m else None
            solicitation_number = (await link_detalhes.inner_text()).strip()

            # 2) Title
            title_el = colunas.nth(1).locator("label[name='BidTitleEllipsis']")
            title = (await title_el.inner_text()).strip() if await title_el.count() else None

            # 3) Commodity description
            comm_el = colunas.nth(1).locator("label[name='CommDescEllipsis']")
            commodity_raw = (await comm_el.inner_text()).strip() if await comm_el.count() else ""
            commodity = commodity_raw.replace("Commodity:", "").strip()

            # 4) Type (e.g., IFB, RFP)
            type_text = (await colunas.nth(2).inner_text()).strip()

            # 5) Department (issuing entity)
            department = (await colunas.nth(3).inner_text()).strip()

            # 6) Close date (deadline)
            close_date = (await colunas.nth(4).inner_text()).strip()

            print(f"[LOGS] → {solicitation_number} | {title} | {commodity} | {type_text} | {department} | {close_date}", file=sys.stderr)
            print(f"[LOGS] Extracted bid_id: {bid_id}", file=sys.stderr)

            # --- Build normalized record ----------------------------------------------

            opportunity = {
                "solicitation_number": solicitation_number,
                "bid_id": bid_id,
                "title": title,
                "commodity": commodity,
                "type": type_text,
                "department": department,
                "close_date": close_date,
            }
            opportunities.append(opportunity)

        # Output the list as JSON (stdout contract for downstream pipeline)
        print(json.dumps(opportunities))

        # Close browser gracefully
        await browser.close()


if __name__ == "__main__":
    # Entry point: run main() in asyncio loop
    asyncio.run(main())
