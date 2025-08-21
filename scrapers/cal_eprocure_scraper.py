# /scrapers/cal_eprocure_scraper.py
import asyncio
import hashlib
import json
import sys
from datetime import datetime
from playwright.async_api import async_playwright

OUTPUT_FILE = "./cal_latest.json"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print("Abrindo", file=sys.stderr)
        page = await browser.new_page()
        await page.goto("https://caleprocure.ca.gov/pages/Events-BS3/event-search.aspx", timeout=60000)
        print("✅ Página carregada com sucesso", file=sys.stderr)

        print("Carregando tabela com dados", file=sys.stderr)
        await page.wait_for_selector("#datatable-ready tbody tr")
        

        # Pega todas as linhas
        print("Pegando as linhas", file=sys.stderr)
        rows = await page.query_selector_all("#datatable-ready tbody tr")

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

        qtd = 20

        opportunities = []
        for row in rows[:qtd]:
            event_id = await row.query_selector("[data-if-label='tdEventId']")
            event_name = await row.query_selector("[data-if-label='tdEventName']")
            dep_name = await row.query_selector("[data-if-label='tdDepName']")
            end_date = await row.query_selector("[data-if-label='tdEndDate']")
            status = await row.query_selector("[data-if-label='tdStatus']")
            department = (await dep_name.inner_text()).strip() if dep_name else None
            evnt_id = (await event_id.inner_text()).strip() if event_id else None


            dep_id = department_map.get(department, "undefined")
            link = f"https://caleprocure.ca.gov/event/{dep_id}/{evnt_id}"
            #print(link)
            

            opportunity = {
                "event_id": (await event_id.inner_text()).strip() if event_id else None,
                "event_name": (await event_name.inner_text()).strip() if event_name else None,
                "department": (await dep_name.inner_text()).strip() if dep_name else None,
                "end_date": (await end_date.inner_text()).strip() if end_date else None,
                "status": (await status.inner_text()).strip() if status else None,
                "link": link
            }
            opportunities.append(opportunity)

        # print("🔎 Primeiras oportunidades extraídas:")
        # for opp in opportunities:
        #     print(opp)

        print(json.dumps(opportunities))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
