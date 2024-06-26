import asyncio
import datetime
import time
from pathlib import Path
import web_scraper
from config import AppConfig, AppConfig_test
from data_processing import *
import openpyxl

async def main():
    print('hello')
    start = time.time()

    config = AppConfig_test('scraper.ini')

    test = web_scraper.WebScraper(config, connections_limit=50)
    await test.run_scraping()
    data = await test.get_data()

    current_time = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M")
    csv_filename = f'{await test.get_module()}--{await test.get_lesson()}--{current_time}.xlsx'

    process_and_save_data(data, csv_filename)

    end = time.time()
    print("[TIME]The time of execution of above program is :",
          (end - start), "s")

if __name__ == "__main__":
    asyncio.run(main())
    #testing()

