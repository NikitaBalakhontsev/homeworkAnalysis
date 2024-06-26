class AuthenticationError(Exception):
    def __init__(self, status_code, message="Ошибка аутентификации", url=None, data=None):
        self.status_code = status_code
        self.url = url
        self.data = data
        self.message = f"{message}. Статус-код: {self.status_code}. URL: {self.url}. Данные авторизации: {self.data}"
        super().__init__(self.message)

