# /scrapers/cal_eprocure_scraper.py
import asyncio
import hashlib
import os
import json
import sys
from datetime import datetime
from playwright.async_api import async_playwright

# File path where raw results can be written if needed
OUTPUT_FILE = "./cal_latest.json"


async def main():
    qtd = int(os.getenv("SCRAPE_CAL_QTY", "20"))         # <-- from env
    headless = os.getenv("HEADLESS", "true").lower() == "true"
    """
    Scraper for Cal eProcure opportunities.

    Flow:
      1. Launch a headless Chromium browser using Playwright.
      2. Navigate to the Cal eProcure event search page.
      3. Wait for the data table with event rows to load.
      4. Extract relevant fields for the first N rows (event_id, name, dept, deadline, status).
      5. Map department names to internal numeric IDs to build official event links.
      6. Output the list of opportunities as JSON to stdout.

    This scraper is used as one of the two required data sources for the aggregator
    (Cal eProcure + SAM.gov) as described in the assignment.
    """

    async with async_playwright() as p:
        # Launch Chromium in headless mode (no visible UI)
        browser = await p.chromium.launch(headless=headless)
        print("Abrindo", file=sys.stderr)

        # Open a new browser page
        page = await browser.new_page()

        # Navigate to Cal eProcure event search page
        await page.goto("https://caleprocure.ca.gov/pages/Events-BS3/event-search.aspx", timeout=60000)
        print("✅ Página carregada com sucesso", file=sys.stderr)

        # Wait until the table with data rows is fully available
        print("Carregando tabela com dados", file=sys.stderr)
        await page.wait_for_selector("#datatable-ready tbody tr")
        
        # Extract all rows from the table body
        print("Pegando as linhas", file=sys.stderr)
        rows = await page.query_selector_all("#datatable-ready tbody tr")

        # Mapping of department display names → internal numeric codes.
        # Used to construct valid event detail links.
        department_map = {
            "Business & Economic Developmnt": "509",
            "Ofc Technology and Solutions I": "531",
            "Gov's Off of Lnd Use & Clmt In": "650",
            "Department of Justice": "820",
            "State Controller": "840",
            "CA State Lottery Commission": "850",
            "State Board of Equalization": "860",
            "Secretary of State": "890",
            "HOPE for Children Trust Acct": "957",
            "Pollution Control Fin Auth": "974",
            "California ABLE Act Board": "981",
            "Dept of Finan Protec and Innov": "1701",
            "Housing & Community Developmnt": "2240",
            "CA Transportation Commission": "2600",
            "Department of Transportation": "2660",
            "Dept of the CA Highway Patrol": "2720",
            "Department of Motor Vehicles": "2740",
            "CA African American Museum": "3105",
            "CA Conservation Corps": "3340",
            "Department of Conservation": "3480",
            "CAL FIRE": "3540",
            "Department of Fish & Wildlife": "3600",
            "State Coastal Conservancy": "3760",
            "Dept of Parks & Recreation": "3790",
            "SF Bay Conservation Commission": "3820",
            "Department of Water Resources": "3860",
            "Health Care Access and Informa": "4140",
            "Dept of Managed Health Care": "4150",
            "California Department of Aging": "4170",
            "State Dept Hlth Care Services": "4260",
            "Department of Public Health": "4265",
            "Dept of Developmental Services": "4300",
            "Department of State Hospitals": "4440",
            "CA Health Benefit Exchange": "4800",
            "Department of Rehabilitation": "5160",
            "Department of Social Services": "5180",
            "Dept of Corrections & Rehab": "5225",
            "State & Community Corrections": "5227",
            "Prison Industry Authority": "5420",
            "Department of Education": "6100",
            "School for the Deaf-Riverside": "6250",
            "State Summer School for Arts": "6255",
            "Institute for Regenerative Med": "6445",
            "UC Davis Medical Center": "6511",
            "UCLA": "6530",
            "CSU, San Bernardino": "6660",
            "CSU, Long Beach": "6740",
            "CSU, Sacramento": "6780",
            "CSU, San Diego": "6790",
            "CSU, San Francisco": "6800",
            "CSU, San Jose": "6810",
            "Cal-Poly San Luis Obispo": "6820",
            "Employment Development Dept": "7100",
            "Dept of Industrial Relations": "7350",
            "Statewide STPD": "75021",
            "Franchise Tax Board": "7730",
            "Department of General Services": "7760",
            "DGS - Statewide Procurement": "77601",
            "State Teachers' Retirement Sys": "7920",
            "Dept of Food & Agriculture": "8570",
            "Public Utilities Commission": "8660",
            "Military Department": "8940",
            "Dept of Veterans Affairs": "8955",
            "32nd DAA -Costa Mesa": "SS246",
        }

        # Limit: number of rows to scrape (configurable)

        opportunities = []
        # Loop through first N rows and extract event details
        for row in rows[:qtd]:
            event_id = await row.query_selector("[data-if-label='tdEventId']")
            event_name = await row.query_selector("[data-if-label='tdEventName']")
            dep_name = await row.query_selector("[data-if-label='tdDepName']")
            end_date = await row.query_selector("[data-if-label='tdEndDate']")
            status = await row.query_selector("[data-if-label='tdStatus']")

            # Clean text values (strip whitespace) if elements exist
            department = (await dep_name.inner_text()).strip() if dep_name else None
            evnt_id = (await event_id.inner_text()).strip() if event_id else None

            # Map department to numeric ID, default "undefined" if not in dictionary
            dep_id = department_map.get(department, "undefined")

            # Construct official event link using dep_id and evnt_id
            link = f"https://caleprocure.ca.gov/event/{dep_id}/{evnt_id}"
            
            # Build opportunity record
            opportunity = {
                "event_id": (await event_id.inner_text()).strip() if event_id else None,
                "event_name": (await event_name.inner_text()).strip() if event_name else None,
                "department": (await dep_name.inner_text()).strip() if dep_name else None,
                "end_date": (await end_date.inner_text()).strip() if end_date else None,
                "status": (await status.inner_text()).strip() if status else None,
                "link": link
            }
            opportunities.append(opportunity)

        # Output the final list of extracted opportunities as JSON
        print(json.dumps(opportunities))

        # Gracefully close the browser
        await browser.close()


if __name__ == "__main__":
    # Run the scraper asynchronously when called directly
    asyncio.run(main())

