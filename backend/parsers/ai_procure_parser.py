# !pip install requests beautifulsoup4 pandas aiohttp nest_asyncio

import re, time, random, asyncio, aiohttp, requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import asyncio
import nest_asyncio

BASE_URL = "https://goszakup.gov.kz"
PAGINATION_URL_TEMPLATE = BASE_URL + "/ru/search/announce?count_record=2000&page={}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
}

# ------------------------- LIST PARSER -------------------------

def parse_page(page_number):
    url = PAGINATION_URL_TEMPLATE.format(page_number)
    print(f"Парсинг страницы-списка: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе страницы {page_number}: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", {"id": "search-result"})
    if not table or not table.tbody:
        print(f"Таблица с результатами не найдена на странице {page_number}")
        return []

    data = []
    for row in table.tbody.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 7:
            continue

        id_col = cols[0]
        tender_id = id_col.find("strong").get_text(strip=True) if id_col.find("strong") else None
        lots_tag = id_col.find("small")
        lots_count = lots_tag.get_text(strip=True).replace("Лотов:", "").strip() if lots_tag else None

        name_col = cols[1]
        link_tag = name_col.find("a")
        announcement_name = link_tag.get_text(strip=True) if link_tag else None
        relative_link = link_tag.get("href") if link_tag else None
        full_link = urljoin(BASE_URL, relative_link) if relative_link else None

        organizer_tag = name_col.find("small")
        organizer = organizer_tag.get_text(strip=True).replace("Организатор:", "").strip() if organizer_tag else None

        method = cols[2].get_text(" ", strip=True)
        start_date_time = cols[3].get_text(" ", strip=True)
        end_date_time = cols[4].get_text(" ", strip=True)

        amount_tag = cols[5].find("strong")
        amount = amount_tag.get_text(strip=True) if amount_tag else cols[5].get_text(" ", strip=True)

        status = cols[6].get_text(" ", strip=True)

        data.append({
            "ID": tender_id,
            "Наименование объявления": announcement_name,
            "Ссылка": full_link,
            "Лотов": lots_count,
            "Организатор": organizer,
            "Способ": method,
            "Начало приема заявок": start_date_time,
            "Окончание приема заявок": end_date_time,
            "Сумма, тг.": amount,
            "Статус": status
        })

    return data


# ------------------------- DETAIL PARSER -------------------------

def clean_text(x):
    if x is None:
        return None
    return re.sub(r"\s+", " ", x).strip()

def parse_top_block(soup):
    out = {}
    top_fields_map = {
        "Номер объявления": "Детали_Номер объявления",
        "Наименование объявления": "Детали_Наименование объявления",
        "Статус объявления": "Детали_Статус объявления",
        "Дата публикации объявления": "Детали_Дата публикации",
        "Срок начала приема заявок": "Детали_Срок начала приема",
        "Срок окончания приема заявок": "Детали_Срок окончания приема",
    }

    for fg in soup.select("div.form-group"):
        label_tag = fg.select_one("label.control-label")
        input_tag = fg.select_one("input.form-control")
        if not label_tag or not input_tag:
            continue
        label = clean_text(label_tag.get_text())
        val = input_tag.get("value")
        if label in top_fields_map and val is not None:
            out[top_fields_map[label]] = clean_text(val)

    return out

def parse_panel_tables(soup):
    out = {}

    panels = soup.select("div.panel.panel-default")
    for panel in panels:
        heading_div = panel.select_one("div.panel-heading")
        if not heading_div:
            continue
        heading = clean_text(heading_div.get_text(" ", strip=True))

        table = panel.select_one("table")
        if not table:
            continue
        if "Общие сведения" in heading:
            prefix = "Общие_"
        elif "Информация об организаторе" in heading:
            prefix = "Организатор_"
        else:
            prefix = clean_text(heading) + "_"

        for tr in table.select("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if not th or not td:
                continue

            key = clean_text(th.get_text(" ", strip=True))
            li_tags = td.select("li")
            if li_tags:
                val = [clean_text(li.get_text(" ", strip=True)) for li in li_tags if clean_text(li.get_text())]
            else:
                val = clean_text(td.get_text(" ", strip=True))

            if key in ["Кол-во лотов в объявлении", "Сумма закупки"]:
                continue

            out[f"{prefix}{key}"] = val

    return out

def parse_detail_content(soup):
    detail = {}
    detail.update(parse_top_block(soup))
    detail.update(parse_panel_tables(soup))
    return detail


async def fetch_detail_page(session, tender, max_retries=3):
    detail_url = tender.get("Ссылка")
    if not detail_url:
        return tender

    detail_url_general = detail_url + "?tab=general"

    for attempt in range(1, max_retries + 1):
        try:
            async with session.get(
                detail_url_general,
                headers=HEADERS,
                timeout=aiohttp.ClientTimeout(total=25)
            ) as resp:
                
                if resp.status in (429, 500, 502, 503, 504):
                    raise aiohttp.ClientResponseError(
                        request_info=resp.request_info,
                        history=resp.history,
                        status=resp.status,
                        message=f"Retryable status {resp.status}"
                    )

                resp.raise_for_status()
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                detail_data = parse_detail_content(soup)
                return {**tender, **detail_data}

        except Exception as e:
            if attempt == max_retries:
                print(f"[FAIL] {detail_url_general}: {e}")
                return tender
            sleep_s = (2 ** attempt) + random.uniform(0.2, 0.8)
            await asyncio.sleep(sleep_s)


async def run_detail_scraper(all_tenders_data):
    CONNECTIONS_LIMIT = 20
    sem = asyncio.Semaphore(CONNECTIONS_LIMIT)

    connector = aiohttp.TCPConnector(limit=CONNECTIONS_LIMIT, ttl_dns_cache=300)

    async def limited_fetch(session, tender):
        async with sem:
            await asyncio.sleep(random.uniform(0.05, 0.2))
            return await fetch_detail_page(session, tender)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [limited_fetch(session, t) for t in all_tenders_data]
        return await asyncio.gather(*tasks)

#--------Start____________#
PAGES_TO_SCRAPE = [1, 2, 3, 4, 5]

def scrape_tenders_sync():
    all_tenders_data = []

    for page in PAGES_TO_SCRAPE:
        all_tenders_data.extend(parse_page(page))

    print(f"\nСобрано {len(all_tenders_data)} базовых записей. Стартуем detail-enrichment...")
    nest_asyncio.apply()
    start_time = time.time()
    final_data = asyncio.run(run_detail_scraper(all_tenders_data))
    print(f"Detail-enrichment завершён за {time.time() - start_time:.1f} сек")

    return final_data

def main():
    records = scrape_tenders_sync()
    df = pd.DataFrame(records)
    df.to_csv("goszakup_tenders_full_async.csv", index=False, encoding="utf-8-sig")
    print("Сохранено: goszakup_tenders_full_async.csv, строк:", len(df))
    print(df.columns)

if __name__ == "__main__":
    main()