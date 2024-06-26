import aiohttp
import asyncio
import ssl
import certifi
import re
import os
import sys

from aiohttp import ClientSession
from bs4 import BeautifulSoup, SoupStrainer
from pickle import load, dump
from prettytable import PrettyTable
from tqdm import tqdm

from exceptions import AuthenticationError
from config import AppConfig

class WebScraper:
    session: ClientSession

    def __init__(self, config: AppConfig, connections_limit: int = 50):
        self.config = config
        self.custom_params = {
            'status': 'passed',
            'course_id': self.config.course_id,
            'group_id': self.config.group_id
        }
        self.session = None
        self.data = []
        self.task_number = 0
        self.semaphore = asyncio.Semaphore(connections_limit)

    async def _create_session(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/104.0.5112.102 Safari/537.36 OPR/90.0.4480.84 (Edition Yx 08) '
        }
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)

        session = aiohttp.ClientSession(headers=headers, connector=connector)

        self.session = session

    async def _authenticate(self):

        print("[INFO] Попытка авторизации через cookies.")
        await self.load_session_cookies()
        if await self.is_auth():
            print("[INFO] Успешная аутентификация через cookies.")
            return

        print("[INFO] Попытка авторизации через логин/пароль")
        try:
            async with self.session.get('https://api.100points.ru/login') as response:
                html = await response.text()

            soup = BeautifulSoup(html, 'lxml')
            token_input = soup.find('input', {'name': '_token'})
            token_value = token_input['value'] if token_input else None

            data = {
                'email': self.config.email,
                'password': self.config.password,
                '_token': token_value,
            }


            async with self.session.post('https://api.100points.ru/login', data=data) as response:
                response.raise_for_status()

                if await self.is_auth():
                    print("[INFO] Успешная аутентификация.")
                    await self.save_session_cookies()
                else:
                    raise AuthenticationError(
                        status_code=response.status,
                        message='Invalid login/password',
                        url=response.url,
                        data=data
                    )

        except AuthenticationError as e:
            print(f"[ERROR] Authentication failed. Exception {e.message}")
            sys.exit(1)

        except Exception as e:
            print(f"[ERROR] Authentication failed. Exception {e}")
            sys.exit(1)

    async def is_auth(self):
        async with self.session.get('https://api.100points.ru/myself', allow_redirects=False) as response:
            if response.status == 200:
                return True
        return False

    async def close_session(self):
        if self.session:
            await self.session.close()
            print("[INFO] Сессия закрыта.")

    async def save_session_cookies(self):
        cookies = self.session.cookie_jar.filter_cookies('https://api.100points.ru/myself')
        if not cookies:
            print("['WARNING'] cookies not saved")
            return
        filename = f'{self.config.email}.pkl'
        with open(filename, 'wb') as f:
            dump(cookies, f)


    async def load_session_cookies(self):
        try:
            filename = f'{self.config.email}.pkl'
            with open(filename, 'rb') as f:
                cookies = load(f)
                self.session.cookie_jar.update_cookies(cookies)
        except FileNotFoundError:
            print(f'[WARNING] cookies file not found')
        except Exception as e:
            print(f'[ERROR] Could not load cookies. Exception {e}')

    async def _fetch_filter_options(self, filter: str) -> list[dict]:
        filter_selection = None
        max_retries = 5
        retry_interval = 0.5

        for attempt in range(max_retries):
            try:
                async with self.session.get('https://api.100points.ru/student_homework/index',
                                            params=self.custom_params) as response:
                    response.raise_for_status()
                    soup = BeautifulSoup(await response.text(), "lxml")
                    filter_selection = soup.select(f'select.form-control#{filter} option')
                    break

            except aiohttp.ClientError as e:
                print(f"[ERROR] Page not found {response.url} Exception: {e}")

            await asyncio.sleep(retry_interval)

        else:
            print(f"[ERROR] Page not found after {max_retries} attempts. {response.url} ")

        if not filter_selection:
            print(f"[ERROR] Filter {filter} not found")

        options = []
        for option in filter_selection:
            filter_id = int(option['value']) if option['value'] != '' else None
            filter_name = ' '.join(option.stripped_strings) if option.stripped_strings else None

            options.append({f'{filter}': filter_id, f'{filter[:-3]}_name': filter_name})

        return options

    async def set_custom_params_by_filter(self, filter: str):
        filter_options = await self._fetch_filter_options(filter=filter)
        available_ids = sorted([option[filter] for option in filter_options if option[filter] is not None])
        param = None

        while param not in available_ids:
            print("\n\n")
            for option in filter_options:
                print(f"{option[filter]} -- {option[f'{filter[:-3]}_name']}")
            print("Доступные id: ", *available_ids)
            print("Введите доступный id (или оставьте пустым для выбора всех): ")
            param = input()
            if param == "":
                break
            else:
                param = int(param)

        self.custom_params[filter] = param

    async def _get_pages_count(self) -> int:
        async with self.semaphore:
            async with self.session.get(url='https://api.100points.ru/student_homework/index',
                                        params=self.custom_params) as response:
                print(f"[INFO] Итоговый запрос: {response.url}")
                html = await response.text()

        soup = BeautifulSoup(html, 'lxml')
        pages_count = 0
        try:
            expected_block = soup.find('div', id="example2_info")

            if expected_block:
                expected = int(re.search(r'\d*$', expected_block.text.strip()).group())
                pages_count = (expected // 15)
                print("\n[INFO] Найдено ", expected, f" записи. Ожидается {pages_count} страниц(ы)")
        except ValueError as e:
            print(f"\n[ERROR] pagination not found. Exception {e}")

        return pages_count

    async def _get_page_data(self, page_number: int):
        page_params = {**self.custom_params, 'page': page_number}

        async with self.semaphore:
            try:
                async with self.session.get(url='https://api.100points.ru/student_homework/index',
                                            params=page_params) as response:
                    html = await response.text()
            except Exception as e:
                print(f'[ERROR] Page {page_number} canceled. Exception {e}')
                return None

        only_links_in_wrapper = SoupStrainer(id='example2_wrapper')
        soup = BeautifulSoup(html, 'lxml', parse_only=only_links_in_wrapper)
        homework_links = [link.get('href') for link in soup.select('tbody tr.odd a[href]')]
        if not homework_links:
            print(f'[ERROR] No homeworks found. Check {response.url}')
            return None
        return homework_links

    @staticmethod
    def _extract_value(elem, attribute=None, regex=None, group=0):
        try:
            value = elem.text.strip()
            if attribute:
                value = elem.get(attribute)
            elif regex:
                value = re.search(regex, value).group(group)
            return value
        except AttributeError:
            return None

    async def _get_homework_data(self, url):
        number = self.task_number
        self.task_number += 1

        async with self.semaphore:
            try:
                async with self.session.get(url=url) as response:
                    html = await response.text()
            except Exception as e:
                print(f'[ERROR] task {number} canceled. Exception {e}')
                return None
        soup = BeautifulSoup(html, 'lxml')
        rows = soup.find('div', class_='card-body').find('div', class_='row').find_all('div',
                                                                                       class_='form-group col-md-3')

        user = rows[0]
        homework = rows[1].find_all('div')
        status = rows[2]
        datetime = rows[3].find_all('div')
        score = rows[4].find_all('div')
        result = rows[5].find_all('div')

        data_dict = {
            "href": url,
            "user_email": self._extract_value(user, regex=r'\S+@+\S+'),
            "user_name": self._extract_value(user.find('input', class_='form-control'), attribute='value'),
            "vk_id": self._extract_value(user.find_all('div')[1], regex=r'(\d+)'),
            "lesson": self._extract_value(homework[0], regex=r'Урок:\s*(.*)', group=1),
            "module": self._extract_value(homework[1], regex=r'Модуль:\s*(.*)', group=1),
            "course": self._extract_value(homework[2], regex=r'Курс:\s*(.*)', group=1),
            "level": self._extract_value(homework[3], regex=r'Сложность:\s*(.*)', group=1),
            "status": self._extract_value(status, regex=r'Статус\s*(.*)', group=1),
            "submission_time": self._extract_value(datetime[0], regex=r'\d+.\d+.\d+\s+\d+:\d+:\d+'),
            "deadline_time": self._extract_value(datetime[2], regex=r'\d+.\d+.\d+\s+\d+:\d+:\d+'),
            "test_score": self._extract_value(score[0], regex=r'\d+'),
            "secondary_score": self._extract_value(score[1], regex=r'\d+'),
            "curator_score": self._extract_value(score[2], regex=r'\d+'),
            "result_score": self._extract_value(result[0], regex=r'\d+%+\s+\d+/+\d+'),
        }
        self.data.append(data_dict)

    async def get_data(self):
        return self.data

    async def get_module(self):
        return self.custom_params['module_id'] or 0

    async def get_lesson(self):
        return self.custom_params['lesson_id'] or 0
    async def print_table(self):
        if len(self.data) == 0:
            print('[WARNING] data is empty')
        fields = list(self.data[0].keys())
        table = PrettyTable(fields)
        for entry in self.data:
            table.add_row([entry[field] for field in fields])

        print(table)

    async def _run_tasks_with_progress(self, task_generator, desc):
        if task_generator is None:
            return None

        tasks = list(task_generator)
        with tqdm(total=len(tasks), desc=desc) as progress_bar:
            return await asyncio.gather(*[self._progress_wrapper(task, progress_bar) for task in tasks])

    async def _progress_wrapper(self, task, progress_bar):
        result = await task
        progress_bar.update(1)
        return result

    async def run_scraping(self):
        try:
            await self._create_session()
            if await self.is_auth() is False:
                await self._authenticate()

            await self.set_custom_params_by_filter(filter='module_id')
            await self.set_custom_params_by_filter(filter='lesson_id')

            task_generator = (
                self._get_page_data(page_number) for page_number in range(1, await self._get_pages_count() + 2)
            )
            all_homework_urls = await self._run_tasks_with_progress(task_generator, "Getting links")

            task_generator = (
                self._get_homework_data(url) for page_urls in all_homework_urls if page_urls is not None for url in page_urls
            )
            await self._run_tasks_with_progress(task_generator, "Getting homeworks")


            if self.config.show_homeworks_in_the_terminal:
                await self.print_table()


        except Exception as e:
            print(e)

        finally:
            await self.close_session()







