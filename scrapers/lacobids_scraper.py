# /scrapers/cal_eprocure_scraper.py
import asyncio
import re
import sys
import json

from playwright.async_api import async_playwright

OUTPUT_FILE = "./cal_latest.json"

async def main():
    async with async_playwright() as p:

        print("[LOGS] Abrindo o Chromium", file=sys.stderr)
        browser = await p.chromium.launch(headless=True)

        print("[LOGS] Abrindo nova página do google", file=sys.stderr)
        page = await browser.new_page()
        link = "https://camisvr.co.la.ca.us/LACoBids/BidLookUp/OpenBidList"
        print(f"[LOGS] Entrando no link: {link}", file=sys.stderr)
        await page.goto(link, timeout=60000)

        opportunities = []

        qtd = 20
        for c in range(qtd):

            await page.select_option("select[ng-model='main.PageSizeSelect']", "100")
            # Dá tempo pro Angular atualizar a tabela
            #await page.wait_for_timeout(1000)  # ajuste se necessário

            print(f"[LOGS] Página carregada com sucesso", file=sys.stderr)

            print(f"[LOGS] Esperando renderizar a tabela", file=sys.stderr)
            await page.wait_for_selector("#searchTbl1 tr")
            print("[LOGS] Achou a tabela", file=sys.stderr)

            # Use LOCATOR (dinâmico) em vez de pegar handles fixos
            linhas = page.locator("#searchTbl1 > tr")
            total = await linhas.count()
            #qtd = min(20, total)
            

            print(f"[LOGS] Linhas encontradas: {total} (processando {qtd})", file=sys.stderr)

            

        
            print(f"[LOGS] Processando linha {c+1}/{qtd}", file=sys.stderr)
            

            linha = linhas.nth(c)

            colunas = linha.locator("td")
            #print(f"[DEBUG] Linha {c}: {await colunas.count()} colunas")


            # 1) Solicitation number + bid_id
            link_detalhes = colunas.nth(0).locator("a[data-content='Select solicitation']")
            href_value = await link_detalhes.get_attribute("href")
            m = re.search(r"selectBid\('(\d+)'\)", href_value or "")
            bid_id = m.group(1) if m else None

            solicitation_number = (await link_detalhes.inner_text()).strip()

            # 2) Title
            title_el = colunas.nth(1).locator("label[name='BidTitleEllipsis']")
            title = (await title_el.inner_text()).strip() if await title_el.count() else None

            # 3) Commodity
            comm_el = colunas.nth(1).locator("label[name='CommDescEllipsis']")
            commodity_raw = (await comm_el.inner_text()).strip() if await comm_el.count() else ""
            commodity = commodity_raw.replace("Commodity:", "").strip()

            # 4) Type
            type_text = (await colunas.nth(2).inner_text()).strip()

            # 5) Department
            department = (await colunas.nth(3).inner_text()).strip()

            # 6) Close date
            close_date = (await colunas.nth(4).inner_text()).strip()


            print(f"[LOGS] → {solicitation_number} | {title} | {commodity} | {type_text} | {department} | {close_date}", file=sys.stderr)
            print(f"[LOGS] bid_id extraído: {bid_id}", file=sys.stderr)









            # print(f"[LOGS] Clicando no link da solicitação {solicitation_number}…")
            # # abre a página de detalhes em nova aba/janela
            # await link_detalhes.click()
            # print(f"[LOGS] Clique realizado, aguardando detalhes na mesma página")
            # new_page = page

            # # Aguarda o painel com os detalhes abrir
            # print(f"[LOGS] Esperando carregar a tabela")
            # await new_page.wait_for_selector("#collapseBidDetail .panel-body")

            # print(f"[LOGS] Pegando os dados...")
            # # Captura os campos principais
            # solicitation_number = (await new_page.locator("text=Solicitation Number:").locator("xpath=../following-sibling::td").inner_text()).strip()
            # title = (await new_page.locator("text=Title:").locator("xpath=../following-sibling::td").inner_text()).strip()
            # department = (await new_page.locator("text=Department:").locator("xpath=../following-sibling::td").inner_text()).strip()
            # bid_type = (await new_page.locator("text=Bid Type:").locator("xpath=../following-sibling::td").first.inner_text()).strip()
            # bid_amount = (await new_page.locator("text=Bid Amount:").locator("xpath=../following-sibling::td").first.inner_text()).strip()
            # commodity = (await new_page.locator("text=Commodity:").locator("xpath=../following-sibling::td").inner_text()).strip()

            # # O texto de descrição está em um <span> cheio de <br>, então extrai como HTML ou texto direto
            # description = (await new_page.locator("#CollapseBidDetailDesc span").inner_text()).strip()

            # # Outros campos simples
            # open_date = (await new_page.locator("text=Open Day:").locator("xpath=../following-sibling::td").first.inner_text()).strip()
            # close_date = (await new_page.locator("text=Close Date:").locator("xpath=../following-sibling::td").first.inner_text()).strip()
            # contact_name = (await new_page.locator("text=Contact Name:").locator("xpath=../following-sibling::td").first.inner_text()).strip()
            # contact_phone = (await new_page.locator("text=Contact Phone:").locator("xpath=../following-sibling::td").first.inner_text()).strip()
            # contact_email = (await new_page.locator("text=Contact Email:").locator("xpath=../following-sibling::td").inner_text()).strip()
            # last_changed = (await new_page.locator("text=Last Changed On:").locator("xpath=../following-sibling::td").inner_text()).strip()

            # print(f"[LOGS] Voltando a página")
            # #await new_page.go_back()
            # # await new_page.click("button[ng-click='main.returnToSearch()']")
            # # await page.wait_for_selector("#searchTbl1 tr")


            # opportunity_details = {
            #     "solicitation_number": solicitation_number,
            #     "bid_id": bid_id,
            #     "title": title,
            #     "commodity": commodity,
            #     "type": type_text,
            #     "department": department,
            #     "close_date": close_date,
            #     "bid_type": bid_type,
            #     "bid_amount": bid_amount,
            #     "description": description,
            #     "open_date": open_date,
            #     "contact_name": contact_name,
            #     "contact_phone": contact_phone,
            #     "contact_email": contact_email,
            #     "last_changed": last_changed,
            # }
            # opportunities.append(opportunity_details)
            #print(opportunity_details)








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



        # print("🔎 Primeiras oportunidades extraídas:")
        # for opp in opportunities:
        #     print(opp)
        print(json.dumps(opportunities))
        

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
