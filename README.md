# PyEasyVKbot

Library for writing bots for VK. Automatic logging, keyboard support, work with API and database

## Deploy locally:

> Install Python(If it's not installed)<br>
> [Download Python3](https://www.python.org/downloads/)

Clone the repository and go to installed folder
```
git clone https://github.com/Ryize/pyeasyvkbot.git
cd pyeasyvkbot
```

Install requirements
```
pip3 install -r requirements.txt
```

Create files start.py and server.py.
In the server.py file, create a new class, it must inherit from VkBot(release.VkBot). In the created class, create the required command.
In start.py, call the class created in server.py and pass in the required parameters.
set up a dictionary with all commands (Required fields: command, comment).
Below is an example program:

> server.py
```
from release import VkBot


class Server(VkBot):
    """
    All the bot logic is the upper level of the system, inherited from the parents
    providing the necessary functionality and allowing you to focus only on writing business logic
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

Run the bot
```
python3 start.py
```

The library works on multithreading, each of your commands will be run in a separate thread

We have already implemented the help, killbot commands (Command to disable the bot).
In case of an error, the logs will be written to the logs folder, a new file every day at 00:00

> The library involves writing a project in the OOP style

> A class (VkBot) is created in release.py that already has all the functions of the library, if you want to create your own solution, use the classes from core.utils

> This library is an add-on for vk-api

> Technologies used in the project: Python3, vk-api, threading, loguru, requests, json, re.
