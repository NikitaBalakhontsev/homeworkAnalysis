import configparser
from pathlib import Path

class AppConfig:
    def __init__(self, config_file_name):
        self.config = configparser.ConfigParser()
        self.config.read(Path(config_file_name))

        # Получаем параметры из [main]
        self.email = self.config.get('main', 'email')
        self.password = self.config.get('main', 'password')
        self.course_id = int(self.config.get('main', 'course_id'))
        self.group_id = int(self.config.get('main', 'group_id'))

        # Получаем параметры из [setting]
        self.filling_in_the_template = self.config.getboolean('setting', 'filling_in_the_template')
        self.show_homeworks_in_the_terminal = self.config.getboolean('setting', 'show_homeworks_in_the_terminal')



class AppConfig_test:
    def __init__(self, config_file_name):
        self.need_overwrite = False
        self.config_file_name = Path(config_file_name)
        self.config = configparser.ConfigParser()
        self._load_config()



    def _load_config(self):
        result = self.config.read(self.config_file_name)
        if not result:
            print(f"[ERROR] Файл конфигурации '{self.config_file_name}' не найден или пуст.")
            print("Сейчас вам будет предложено заполнить новый файл конфигурации")

        try:
            # Получаем параметры из [main]
            self.email = self._get_config_value('main', 'email')
            self.password = self._get_config_value('main', 'password')

            self.course_id = self._get_config_value('main', 'course_id', data_type=int)
            self.group_id = self._get_config_value('main', 'group_id', data_type=int)

            # Получаем параметры из [setting]
            self.filling_in_the_template = self._get_config_value('setting', 'filling_in_the_template', data_type=bool)
            self.show_homeworks_in_the_terminal = self._get_config_value('setting', 'show_homeworks_in_the_terminal', data_type=bool)

        except Exception as e:
            print(f"[ERROR] Ошибка чтения конфигурационного файла: {e}")

        finally:
            if self.need_overwrite:
                self._save_config()

    def _get_config_value(self, section, option, data_type=None):
        value = self.config.get(section, option, fallback=None)

        if not _is_validate(value):
            value = self.get_by_user(option, data_type)

            if self.config.has_section(section) is False:
                self.config.add_section(section)
            self.config.set(section, option, value)
            self.need_overwrite = True

        return value

    @staticmethod
    def get_by_user(option, data_type=None):

        while True:
            user_input = input(f"Введите значение для параметра '{option}'  ")
            if _is_validate(user_input, data_type):
                return user_input
            else:
                print(f"[ERROR] Введено значение типа {type(user_input)}")



    '''
    def _prompt_user_for_config_values(self):
        self.need_overwrite = True
        options_to_prompt = [
            ("email", str),
            ("password", str),
            ("course_id", int),
            ("group_id", int),
            ("filling_in_the_template", str),
            ("show_homeworks_in_the_terminal", str),
        ]

        for option, cast_func in options_to_prompt:
            value = self.get_by_user(option, cast_func)
            setattr(self, option, value)
    '''

    def _save_config(self):
        with open(self.config_file_name, 'w') as config_file:
            print(f"Writing config to file: {self.config_file_name}")
            self.config.write(config_file)
            print("Config successfully written.")


def _is_validate(option, data_type=None):
    if option is None:
        return False

    if data_type is None:
        return True

    elif data_type == bool:
        return option.lower() in ['true', '1', 't', 'y', 'yes', 'false', '0', 'n', 'no', '']
    elif data_type == int:
        try:
            int(option)
            return True
        except ValueError:
            return False
    else:
        return False