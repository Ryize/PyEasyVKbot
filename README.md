# PyEasyVKbot

Библиотека для написания ботов для ВКонтакте. Готова ООП архитектура, встроенные команды, поддержка клавиатуры, работа с API и базой данных.

## Прежде всего:

> Установите Python (если он не установлен)<br>
> [Скачать Python3](https://www.python.org/downloads/)

Клонируйте репозиторий и перейдите в установленную папку:
```
git clone https://github.com/Ryize/pyeasyvkbot.git
cd pyeasyvkbot
```

Установите requirements:
```
pip3 install -r requirements.txt
```

Создайте файлы start.py и server.py .
В самом server.py создайте новый класс, он должен наследоваться от VkBot (release.VkBot). В этом классе создайте необходимую команду.
В start.py, вызовите класс, созданный в server.py и передайте необходимые параметры.
Настройте словарь указав необходимые параметры (обязательные поля: command, comment).
Ниже приведен пример программы:

> server.py
```
from release import VkBot


class Server(VkBot):
    """
    Вся логика бота - это верхний уровень системы, унаследованный от VkBot,
    обеспечивающий необходимую функциональность и позволяющий сосредоточиться только на написании бизнес-логики
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def command_ping(self, send_id: int) -> None:
        self.send_msg(send_id, message='Понг!')

    def command_helpop(self, send_id: int):
        text_in_msg = self.get_command_text(self._text_in_msg, self._command_args)
        if not text_in_msg:
            self.send_msg(send_id,
                          message=f'⛔️ Ваше обращение не может быть пустым!')
            return
        self.send_msg(send_id,
                      message=f'✅ Ваше обращение принято.\nАдминистрация рассмотрит его и ответит Вам в ближайшее время')
        self.send_admin_msg(
            f"👤 Пользователь написал: {text_in_msg}\n\n📞Для ответа ему используйте такой id: {send_id}")
```

> start.py
```
if __name__ == '__main__':
    from server import Server

    server = Server(api_token='YOUR TOKEN', group_id=id_int, debug=True)

    server.admins = [your_vk_id_int]

    COMMANDS = {
        '/help': {
            'command': server.command_ping,
            'comment': 'Получить список всех команд',
        },
        'Начать *nshow': {
            'command': server.command_help,
            'comment': 'Получить список всех команд',
        },
        '🔎Помощь *nshow': {
            'command': server.get_bot_info,
            'comment': 'Получить список всех команд',
        },
        '/ping': {
            'command': server.command_ping,
            'comment': 'Проверить работоспособность бота',
        }
    }
    while True:
        server.start(COMMANDS)
```

Запустите бота:
```
python3 start.py
```

Библиотека работает в режиме многопоточности, каждая из ваших команд будет выполняться в отдельном потоке.

Мы уже внедрили команды help, killbot (команда для отключения бота).
В случае возникновения ошибки, она будет записана в файл директории logs, новый файл каждый день в 00:00.

> Библиотека предполагает написание проекта в стиле ООП

> Класс (VkBot) создается в release.py в котором уже есть все функции библиотеки, если вы хотите создать свое собственное решение, используйте классы из  core.utils

> Эта библиотека является надстройкой к vk-api

> Технологии, использованные в проекте: Python3, vk-api, threading, loguru, requests, json, re.
