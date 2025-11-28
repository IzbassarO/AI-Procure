"""
ФИНАЛЬНЫЙ ПАРСЕР ТЕНДЕРОВ REESTR.NADLOC.KZ
Создает ТРИ CSV файла:
1. tenders_list.csv - список тендеров из таблицы реестра
2. completed_tenders.csv - детали ЗАВЕРШЕННЫХ тендеров (протоколы)
3. published_tenders.csv - детали ОПУБЛИКОВАННЫХ тендеров (объявления)
"""

import aiohttp
import asyncio
import csv
from bs4 import BeautifulSoup
from datetime import datetime
import ssl
from typing import List, Dict, Optional
import logging
import re
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedTenderParser:
    """Продвинутый парсер с автоопределением типа тендера"""

    def __init__(self, base_url: str = "https://www.reestr.nadloc.kz"):
        self.base_url = base_url
        self.session = None
        self.tenders_list = []
        self.completed_tenders = []  # Завершенные
        self.published_tenders = []  # Опубликованные
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        }

    async def __aenter__(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=5)
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers=self.headers,
            timeout=timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            await asyncio.sleep(0.25)

    async def fetch_page(self, url: str, retry: int = 3) -> Optional[str]:
        """Получение HTML страницы"""
        for attempt in range(retry):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Статус {response.status} для {url}")
            except Exception as e:
                logger.error(f"Ошибка при загрузке {url}: {e}")
                if attempt < retry - 1:
                    await asyncio.sleep(2 ** attempt)
        return None

    # =========================================================================
    # ПАРСИНГ СПИСКА ТЕНДЕРОВ
    # =========================================================================

    def parse_tender_list_table(self, html: str) -> List[Dict]:
        """Парсинг основной таблицы"""
        soup = BeautifulSoup(html, 'html.parser')
        tenders = []

        table = soup.find('table')
        if not table:
            return []

        rows = table.find_all('tr')[1:]
        logger.info(f"Найдено {len(rows)} строк")

        for idx, row in enumerate(rows, 1):
            try:
                tender = self.parse_tender_row(row)
                if tender:
                    tenders.append(tender)
                    logger.info(f"  ✓ [{idx}] {tender.get('code', 'N/A')[:50]}")
            except Exception as e:
                logger.error(f"  ✗ Ошибка строки {idx}: {e}")

        return tenders

    def parse_tender_row(self, row) -> Optional[Dict]:
        """Парсинг строки таблицы"""
        cells = row.find_all('td')
        if len(cells) < 7:
            return None

        tender = {}

        try:
            code_cell = cells[0]
            link = code_cell.find('a', href=True)
            if link:
                tender['code'] = link.get_text(strip=True)
                tender['detail_link'] = urljoin(self.base_url, link['href'])
                tender['description'] = code_cell.get_text(strip=True).replace(tender['code'], '').strip()
            else:
                tender['code'] = code_cell.get_text(strip=True)
                tender['detail_link'] = None

            tender['customer'] = cells[1].get_text(strip=True)
            tender['lots'] = cells[2].get_text(strip=True)
            tender['planned_amount'] = cells[3].get_text(strip=True) or '-'
            tender['purchase_amount'] = cells[4].get_text(strip=True)
            tender['method'] = cells[5].get_text(strip=True)

            status_cell = cells[6]
            tender['status'] = status_cell.get_text(strip=True)

            if len(cells) >= 8:
                tender['dates'] = cells[7].get_text(strip=True)

            return tender
        except Exception as e:
            logger.error(f"Ошибка парсинга строки: {e}")
            return None

    async def parse_page_list(self, page_num: int) -> List[Dict]:
        """Парсинг страницы списка"""
        url = f"{self.base_url}/ru/tender/list?page={page_num}"
        logger.info(f"\n{'=' * 70}")
        logger.info(f"СТРАНИЦА {page_num}: {url}")
        logger.info(f"{'=' * 70}")

        html = await self.fetch_page(url)
        if not html:
            return []

        tenders = self.parse_tender_list_table(html)
        logger.info(f"✓ Получено {len(tenders)} тендеров")

        return tenders

    # =========================================================================
    # ОПРЕДЕЛЕНИЕ ТИПА ТЕНДЕРА И ПАРСИНГ
    # =========================================================================

    async def parse_tender_detail(self, tender: Dict) -> Dict:
        """Парсинг детальной информации с определением типа"""
        detail_link = tender.get('detail_link')
        if not detail_link:
            return {}

        tender_code = tender.get('code', 'N/A')
        logger.info(f"  → {tender_code[:50]}")

        html = await self.fetch_page(detail_link)
        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()

        # Определяем тип тендера
        is_completed = any(x in text for x in [
            'Протокол подведения итогов',
            'способом из одного источника',
            'Предмет приобретения ТРУ способом'
        ])

        is_published = any(x in text for x in [
            'Время начала и окончания представления',
            'Дата и время вскрытия',
            'Предмет закупа способом через систему'
        ])

        if is_completed:
            logger.info(f"    ℹ️ Тип: ЗАВЕРШЕННЫЙ")
            detail = self.parse_completed_tender(soup, text, tender_code, detail_link)
            return {'type': 'completed', 'data': detail}
        elif is_published:
            logger.info(f"    ℹ️ Тип: ОПУБЛИКОВАННЫЙ")
            detail = self.parse_published_tender(soup, text, tender_code, detail_link)
            return {'type': 'published', 'data': detail}
        else:
            logger.warning(f"    ⚠️ Неизвестный тип")
            return {'type': 'unknown', 'data': {}}

    # =========================================================================
    # ПАРСИНГ ЗАВЕРШЕННЫХ ТЕНДЕРОВ
    # =========================================================================

    def parse_completed_tender(self, soup, text: str, tender_code: str, link: str) -> Dict:
        """Детальный парсинг ЗАВЕРШЕННОГО тендера"""
        detail = {
            'tender_code': tender_code,
            'detail_link': link
        }

        try:
            # 1. Наименование заказчика
            match = re.search(r'1\.\s*Наименование заказчика[:\s]*(.*?)(?=\n2\.|\n\n)', text, re.DOTALL)
            if match:
                detail['customer_name'] = match.group(1).strip()

            # 2. Местонахождение
            match = re.search(r'2\.\s*Местонахождение заказчика[:\s]*(.*?)(?=\n3\.|\n\n)', text, re.DOTALL)
            if match:
                detail['customer_location'] = match.group(1).strip()[:500]

            # 3. Основание для закупа
            match = re.search(r'3\.\s*Основание для закупа.*?:(.*?)(?=\n4\.|\n\n)', text, re.DOTALL)
            if match:
                detail['purchase_basis'] = match.group(1).strip()[:1000]

            # 4. Предмет приобретения - может быть несколько лотов
            lots_section = re.search(r'4\.\s*Предмет приобретения.*?(?=5\.|$)', text, re.DOTALL)
            if lots_section:
                lots_text = lots_section.group(0)

                # Извлекаем все лоты
                lot_patterns = re.findall(
                    r'Номер и наименование лота:\s*(\d+),\s*(.*?)\s*Сумма.*?(\d[\d\s,.]+)\s*тенге', lots_text,
                    re.DOTALL)

                if lot_patterns:
                    lots_info = []
                    for lot_num, lot_name, lot_sum in lot_patterns:
                        lots_info.append(f"Лот {lot_num}: {lot_name.strip()} - {lot_sum.strip()} тг")
                    detail['lots_description'] = ' | '.join(lots_info)
                    detail['total_lots'] = len(lot_patterns)

                # Извлекаем позиции СКП
                skp_items = []
                tables = soup.find_all('table')
                for table in tables:
                    if 'Код СКП' in table.get_text():
                        rows = table.find_all('tr')[1:]
                        for row in rows[:10]:  # Первые 10 позиций
                            cells = row.find_all('td')
                            if len(cells) >= 4:
                                code = cells[0].get_text(strip=True)
                                descr = cells[1].get_text(strip=True)[:100]
                                unit = cells[2].get_text(strip=True)
                                qty = cells[3].get_text(strip=True)
                                skp_items.append(f"{code}|{descr}|{unit}|{qty}")
                        break

                if skp_items:
                    detail['skp_items'] = ' || '.join(skp_items)

            # 5. Лицензии
            licenses_section = re.search(r'5\.\s*Номера лицензии.*?:(.*?)(?=6\.|$)', text, re.DOTALL)
            if licenses_section:
                licenses_text = licenses_section.group(1)
                licenses = re.findall(r'Лицензия\(контракт\)\s*№\s*(\d+)\s*от\s*([\d.]+)', licenses_text)
                if licenses:
                    lic_list = [f"№{lic[0]} от {lic[1]}" for lic in licenses]
                    detail['licenses'] = ' | '.join(lic_list)

            # 6. Поставщики - извлекаем из таблиц
            suppliers_section = re.search(r'6\.\s*Наименование поставщика.*?(?=7\.|$)', text, re.DOTALL)
            if suppliers_section:
                suppliers = []
                for table in soup.find_all('table'):
                    if 'Наименование' in table.get_text() and 'поставщика' in table.get_text():
                        rows = table.find_all('tr')[1:]
                        for row in rows[:5]:
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                supplier_name = cells[1].get_text(strip=True)[:200]
                                supplier_addr = cells[2].get_text(strip=True)[:200] if len(cells) > 2 else ''
                                delivery_period = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                                delivery_place = cells[4].get_text(strip=True)[:100] if len(cells) > 4 else ''

                                suppliers.append(f"{supplier_name}|{supplier_addr}|{delivery_period}|{delivery_place}")
                        break

                if suppliers:
                    detail['suppliers'] = ' || '.join(suppliers)
                    # Первый обычно победитель
                    if suppliers:
                        parts = suppliers[0].split('|')
                        detail['winner_supplier'] = parts[0]
                        if len(parts) > 1:
                            detail['winner_address'] = parts[1]

            # 7. Цены
            prices_section = re.search(r'7\.\s*Цена, предложенная.*?(?=8\.|$)', text, re.DOTALL)
            if prices_section:
                prices = []
                for table in soup.find_all('table'):
                    if 'Предложенная цена' in table.get_text() or 'предложенная цена' in table.get_text():
                        rows = table.find_all('tr')[1:]
                        for row in rows[:5]:
                            cells = row.find_all('td')
                            if len(cells) >= 3:
                                supplier = cells[1].get_text(strip=True)[:100]
                                price = cells[2].get_text(strip=True)
                                local_content = cells[3].get_text(strip=True) if len(cells) > 3 else ''

                                prices.append(f"{supplier}|{price}|{local_content}")
                        break

                if prices:
                    detail['all_prices'] = ' || '.join(prices)
                    # Первая цена - победитель
                    if prices:
                        parts = prices[0].split('|')
                        detail['winner_price'] = parts[1] if len(parts) > 1 else parts[0]
                        if len(parts) > 2:
                            detail['local_content'] = parts[2]

            # 8. Код закупки
            match = re.search(r'8\.\s*Код закупки[:\s]*([A-Z]+[\w\.\-]+)', text)
            if match:
                detail['purchase_code'] = match.group(1)

            # Подпись
            match = re.search(r'Имя подписавшего:\s*([^\n]+)', text)
            if match:
                detail['signed_by'] = match.group(1).strip()

            match = re.search(r'Дата подписи:\s*(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})', text)
            if match:
                detail['signed_date'] = match.group(1).strip()

            logger.info(f"    ✓ Извлечено {len(detail)} полей")

        except Exception as e:
            logger.error(f"    ✗ Ошибка: {e}")

        return detail

    # =========================================================================
    # ПАРСИНГ ОПУБЛИКОВАННЫХ ТЕНДЕРОВ
    # =========================================================================

    def parse_published_tender(self, soup, text: str, tender_code: str, link: str) -> Dict:
        """Детальный парсинг ОПУБЛИКОВАННОГО тендера"""
        detail = {
            'tender_code': tender_code,
            'detail_link': link
        }

        try:
            # 1. Наименование заказчика
            match = re.search(r'1\.\s*Наименование заказчика.*?\n(.*?)(?=\t|$)', text, re.MULTILINE)
            if match:
                detail['customer_name'] = match.group(1).strip()

            # Адрес интернет ресурса
            match = re.search(r'Адрес интернет ресурса\s*(https?://[\w\.\-/]+)', text)
            if match:
                detail['web_resource'] = match.group(1)

            # Местонахождение
            match = re.search(r'Местонахождение заказчика.*?\n(.*?)(?=\n2\.|\n\n)', text, re.DOTALL)
            if match:
                detail['customer_location'] = match.group(1).strip()[:300]

            # 2. Предмет закупа - извлекаем все позиции из таблицы
            positions = []
            tables = soup.find_all('table')
            for table in tables:
                if 'Код СКП' in table.get_text() and 'Краткое описание' in table.get_text():
                    rows = table.find_all('tr')[1:]

                    for row in rows[:50]:  # Первые 50 позиций
                        cells = row.find_all('td')
                        if len(cells) >= 5:
                            # ЛОТ №, Код СКП, Описание, Единица, Количество, Сумма, Срок, Место
                            lot_num = cells[0].get_text(strip=True) if cells[0].get_text(strip=True) else 'N/A'
                            skp_code = cells[1].get_text(strip=True)
                            description = cells[2].get_text(strip=True)[:100]
                            unit = cells[3].get_text(strip=True)
                            quantity = cells[4].get_text(strip=True)
                            amount = cells[5].get_text(strip=True) if len(cells) > 5 else ''
                            delivery_days = cells[6].get_text(strip=True) if len(cells) > 6 else ''
                            delivery_place = cells[7].get_text(strip=True)[:150] if len(cells) > 7 else ''

                            positions.append(
                                f"{skp_code}|{description}|{unit}|{quantity}|{amount}|{delivery_days}|{delivery_place}")

                    break

            if positions:
                detail['purchase_items'] = ' || '.join(positions)
                detail['total_items'] = len(positions)

            # 3. Время начала и окончания
            match = re.search(r'Дата и время начала.*?\n([\d\.\s:]+)', text)
            if match:
                detail['submission_start'] = match.group(1).strip()

            match = re.search(r'Дата и время окончания.*?\n([\d\.\s:]+)', text)
            if match:
                detail['submission_end'] = match.group(1).strip()

            match = re.search(r'Дата и время вскрытия.*?\n([\d\.\s:]+)', text)
            if match:
                detail['opening_date'] = match.group(1).strip()

            # 4. Контакты
            match = re.search(r'Адрес электронной почты.*?\n([\w\.\-@]+)', text)
            if match:
                detail['contact_email'] = match.group(1).strip()

            match = re.search(r'Номер контактного телефона.*?\n([\d\s\+\(\)]+)', text)
            if match:
                detail['contact_phone'] = match.group(1).strip()

            # 6. Требования по местному содержанию
            match = re.search(r'Требования по местному содержанию.*?\n([\d\s%]+)', text)
            if match:
                detail['local_content_requirement'] = match.group(1).strip()

            # Срок заключения договора
            match = re.search(r'Требуемый срок заключения договора.*?\n(.*?)(?=\t|\n)', text)
            if match:
                detail['contract_deadline'] = match.group(1).strip()

            # Подпись
            match = re.search(r'Имя подписавшего:\s*([^\t\n]+)', text)
            if match:
                detail['signed_by'] = match.group(1).strip()

            match = re.search(r'Дата подписи:\s*(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})', text)
            if match:
                detail['signed_date'] = match.group(1).strip()

            logger.info(f"    ✓ Извлечено {len(detail)} полей")

        except Exception as e:
            logger.error(f"    ✗ Ошибка: {e}")

        return detail

    # =========================================================================
    # ОСНОВНАЯ ЛОГИКА
    # =========================================================================

    async def parse_all(self, start_page: int = 1, end_page: int = 3):
        """Полный парсинг"""
        print("\n" + "=" * 70)
        print("ЭТАП 1: ПАРСИНГ СПИСКА")
        print("=" * 70)

        for page in range(start_page, end_page + 1):
            tenders = await self.parse_page_list(page)
            self.tenders_list.extend(tenders)
            if page < end_page:
                await asyncio.sleep(1)

        logger.info(f"\n✓ Получено {len(self.tenders_list)} тендеров")
        self.save_tenders_list()

        if self.tenders_list:
            print("\n" + "=" * 70)
            print("ЭТАП 2: ПАРСИНГ ДЕТАЛЕЙ")
            print("=" * 70)

            semaphore = asyncio.Semaphore(3)

            async def parse_with_semaphore(tender):
                async with semaphore:
                    return await self.parse_tender_detail(tender)

            tasks = [parse_with_semaphore(t) for t in self.tenders_list]
            results = await asyncio.gather(*tasks)

            # Разделяем по типам
            for result in results:
                if result.get('type') == 'completed':
                    self.completed_tenders.append(result['data'])
                elif result.get('type') == 'published':
                    self.published_tenders.append(result['data'])

            logger.info(f"\n{'=' * 70}")
            logger.info(f"✓ Завершенные: {len(self.completed_tenders)}")
            logger.info(f"✓ Опубликованные: {len(self.published_tenders)}")
            logger.info(f"{'=' * 70}\n")

            self.save_completed_tenders()
            self.save_published_tenders()

    def save_tenders_list(self):
        """Сохранение списка"""
        if not self.tenders_list:
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'tenders_list_{timestamp}.csv'

        fieldnames = ['code', 'description', 'customer', 'lots', 'planned_amount',
                      'purchase_amount', 'method', 'status', 'dates', 'detail_link']

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.tenders_list)

        logger.info(f"\n✅ СПИСОК: {filename} ({len(self.tenders_list)} записей)")
        return filename

    def save_completed_tenders(self):
        """Сохранение завершенных"""
        if not self.completed_tenders:
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'completed_tenders_{timestamp}.csv'

        all_keys = set()
        for t in self.completed_tenders:
            all_keys.update(t.keys())

        priority = ['tender_code', 'customer_name', 'customer_location', 'purchase_basis',
                    'lots_description', 'total_lots', 'skp_items', 'licenses',
                    'winner_supplier', 'winner_address', 'winner_price', 'local_content',
                    'suppliers', 'all_prices', 'purchase_code', 'signed_by', 'signed_date']

        fieldnames = [k for k in priority if k in all_keys]
        fieldnames.extend(sorted(all_keys - set(fieldnames)))

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.completed_tenders)

        logger.info(f"✅ ЗАВЕРШЕННЫЕ: {filename} ({len(self.completed_tenders)} записей)")
        return filename

    def save_published_tenders(self):
        """Сохранение опубликованных"""
        if not self.published_tenders:
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'published_tenders_{timestamp}.csv'

        all_keys = set()
        for t in self.published_tenders:
            all_keys.update(t.keys())

        priority = ['tender_code', 'customer_name', 'customer_location', 'web_resource',
                    'purchase_items', 'total_items', 'submission_start', 'submission_end',
                    'opening_date', 'contact_email', 'contact_phone',
                    'local_content_requirement', 'contract_deadline',
                    'signed_by', 'signed_date']

        fieldnames = [k for k in priority if k in all_keys]
        fieldnames.extend(sorted(all_keys - set(fieldnames)))

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.published_tenders)

        logger.info(f"✅ ОПУБЛИКОВАННЫЕ: {filename} ({len(self.published_tenders)} записей)")
        return filename


async def main():
    print("\n" + "=" * 70)
    print("ПАРСЕР ТЕНДЕРОВ REESTR.NADLOC.KZ")
    print("Создает ТРИ CSV файла:")
    print("  1. tenders_list_*.csv - список тендеров")
    print("  2. completed_tenders_*.csv - завершенные (протоколы)")
    print("  3. published_tenders_*.csv - опубликованные (объявления)")
    print("=" * 70)

    async with AdvancedTenderParser() as parser:
        await parser.parse_all(
            start_page=1,
            end_page=2  # Измените на нужное
        )

        print("\n" + "=" * 70)
        print("✅ ЗАВЕРШЕНО!")
        print(f"📊 Список: {len(parser.tenders_list)}")
        print(f"✅ Завершенные: {len(parser.completed_tenders)}")
        print(f"📢 Опубликованные: {len(parser.published_tenders)}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())