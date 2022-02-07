import requests
import json
import re
import vk_api.vk_api

from typing import Union
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotEventType
from vk_api.bot_longpoll import VkBotLongPoll, VkBotMessageEvent
from vk_api.utils import get_random_id
from loguru import logger

from core.exceptions import AuthError, CommandStopError


class FileDB:
    """
    Сlass that implements the basic logic of working with files, writing, reading, splitting into lists by element, etc.
    this class covers the need for basic file handling
    """

    def __init__(self, file_name: str = 'test.txt', *args, **kwargs):
        self.__file_name = file_name
        super().__init__(*args, **kwargs)

    def write(self, data: str, code: str = 'a'):
        with self.__file_open(code) as file:
            file.write(data + '\n')

    def read(self):
        with self.__file_open('r') as file:
            return file.read()

    def readlines(self):
        with self.__file_open('r') as file:
            return file.read().split('\n')

    def splitter(self, splitter: str = '/'):
        data_list = self.readlines()
        return_values = []
        for string in data_list:
            return_values.append(string.split(splitter))
        return return_values

    def get_by_index(self, index: int = 0, splitter: str = '/'):
        return_values = []
        for i in self.splitter(splitter):
            return_values.append(i[index])
        return return_values

    def get_by_value(self, value: str = '0', splitter: str = '/', index: int = None):
        return_values = []
        try:
            for i in self.splitter(splitter):
                if index is not None:
                    if value == i[index]:
                        return_values.append(i)
                else:
                    for j in i:
                        if value == j:
                            return_values.append(i)
        except IndexError:
            pass
        return return_values

    def __file_open(self, code: str):
        return open(self.__file_name, code)

    @property
    def file_name(self):
        return self.file_name

    @file_name.setter
    def file_name(self, file_name):
        self.file_name = file_name


class LoginManagerMixin:
    """
    Logic of basic work with users, authorization, creating a new user, getting a user by id of VK.
    For work, another class is used FileDB
    """

    def __init__(self, file_name: str = 'test.txt', *args, **kwargs):
        self._user = None
        self.__file_db = FileDB(file_name)
        super().__init__(*args, **kwargs)

    def authenticate(self, id: str = None, login: str = None, password: str = None):
        user_data = self.__file_db.get_by_value(login, index=1)

        if id:
            user = self.__file_db.get_by_value(id, index=0)
            if user:
                self._user = user
                return True

        if user_data:
            for user in user_data:
                if user[2] == password:
                    self._user = user
                    return True
        return False

    def new_user(self, id: str, login: str, password: str):
        self.__file_db.write(f'{id}/{login}/{password}')

    def get_user_by_id(self, id: str):
        return self.__file_db.get_by_value(value=id, index=0)

    def get_user_by_login(self, login: str):
        return self.__file_db.get_by_value(value=login, index=1)

    def get_user_by_groups(self, groups: str):
        return self.__file_db.get_by_value(value=groups, index=2)

    def get_active_user(self):
        return self._user


class APIBackendMixin:
    """
    The logic of working with the API, the logic of receiving data by get, post requests,
    and also converting them to json and back
    """

    def __init__(self, url: str = 'https://127.0.0.1', standart_head: str = '/api/', *args, **kwargs):
        self.url = url
        self.standart_head = standart_head
        self.full_url = url + standart_head
        super().__init__(*args, **kwargs)

    def get(self, page: str = '', json: bool = False, verify: bool = True):
        data = requests.get(self.full_url + page, verify=verify).text
        if json:
            data = self.__to_json(data)
        return data

    def post(self, page: str = '', data: dict = '', json: bool = False):
        data = requests.post(self.full_url + page, data=data, verify=verify).text
        if json:
            data = self.__to_json(data)
        return data

    def __to_json(self, data):
        print(data)
        return json.loads(data)

    @staticmethod
    def remove_html(value):
        return re.sub(r'\<[^>]*\>', '', value)


class KeyboardMixin(VkKeyboard):
    """
    Working with the VK keyboard, implemented methods for
    getting, hiding the keyboard and showing auxiliary commands
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def hide_keyboard(self, label: str = '📌️Вернуть клавиатуру'):
        keyboard = VkKeyboard()
        keyboard.add_button(label=label, color=VkKeyboardColor.POSITIVE)
        return keyboard

    def get_standart_keyboard(self):
        keyboard = VkKeyboard()
        keyboard.add_button(label='🔎Помощь', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button(label='☠️Скрыть клавиатуру', color=VkKeyboardColor.NEGATIVE)
        return keyboard

    def get_help(self):
        keyboard = VkKeyboard()
        keyboard.add_button(label='🔎Помощь', color=VkKeyboardColor.POSITIVE)
        return keyboard


class BotLogger:
    """
     A class that provides the ability to log errors that occur in the program.
     Used by: Loguru.
    """

    logger = logger

    def __init__(self, level: str = 'DEBUG', format: str = '{time} {level} {message}', rotation: str = '00:00'):
        self.logger.add('logs/debug.log', format=format, level=level, rotation=rotation, compression='zip')

    def change_log_settings(self, level: str = 'DEBUG', format: str = '{time} {level} {message}',
                            rotation: str = '00:00'):
        self.logger.add('logs/debug.log', format=format, level=level, rotation=rotation, compression='zip')

    def get_logger(self):
        return self.logger


class BaseStarter:
    """
    The main class for the work of the VK bot.
    Implemented the logic for launching the bot,
    automatically catching errors, applying command parameters, etc.

    Supported command suffixes:
    stop: Do not process this command
    nshow: Не показывать команду в /helpnshow: Don't show command in help
    auth: Require authorization to execute a command
    admin: Command requiring Administrator rights
    args: Indicate if the command has arguments (Example: login Admin, 12345)
    """

    logger = BotLogger().get_logger()

    def __init__(self, api_token, group_id, debug: bool = False, admins: list = [], *args, **kwargs):

        # Для Long Poll
        if admins is None:
            admins = []
        self.__vk = vk_api.VkApi(token=api_token)

        # Для использования Long Poll API
        self._long_poll = VkBotLongPoll(self.__vk, group_id)

        # Для вызова методов vk_api
        self._vk_api = self.__vk.get_api()

        # Режим отладки(Когда он включёт ошибка будет останавливать программу
        self.debug = debug

        # Аргументы команлы
        self._command_args = ''

        # Текст сообщения
        self._text_in_msg = ''

        # Список администраторов
        self.admins = admins

        super().__init__(*args, **kwargs)

    def start(self, commands: dict) -> None:
        """ Запуск бота """

        self.commands = commands
        for event in self._long_poll.listen():  # Слушаем сервер

            # Пришло новое сообщение
            if event.type == VkBotEventType.MESSAGE_NEW:
                self._command_starter(event=event)

    @logger.catch
    def _command_starter(self, event: VkBotMessageEvent) -> None:
        chat_id = event.object.peer_id
        text_in_msg = event.object.text

        self._text_in_msg = text_in_msg
        self.__send_id = chat_id

        for command in self.commands:
            try:
                param = self.__get_args_command(command, text_in_msg)
            except AuthError:
                self._vk_api.messages.send(peer_id=chat_id,
                                           message='🤫Вы не авторизованны! /help',
                                           random_id=get_random_id(),
                                           keyboard=KeyboardMixin().get_help().get_keyboard())
            except CommandStopError:
                self._vk_api.messages.send(peer_id=chat_id,
                                           message='👮Данная команда сейчас не доступна! /help',
                                           random_id=get_random_id(),
                                           keyboard=KeyboardMixin().get_help().get_keyboard())
            if (command.lower() == text_in_msg.lower()) or param:
                self.command = command
                requested_function = self.commands[command]['command']
                requested_function(chat_id)

    @logger.catch
    def __get_args_command(self, command: str, text_in_msg: str) -> Union[None, list]:
        command_args = command.split(' *')[1:]
        command = command.split(' *')[0]

        self._command_args = command

        return_data = []
        try:
            text_in_msg = text_in_msg.split('/')[1]
            command = command.replace('/', '')
        except IndexError:
            pass

        if text_in_msg.split(''.join(command))[0] != '':
            return

        if text_in_msg.find(command) != -1 and command_args.count('stop'):
            raise CommandStopError('Эта команда сейчас не работает!')

        if text_in_msg.find(command) != -1 and command_args.count('nshow') != 0:
            return_data.append(True)

        if text_in_msg.find(command) != -1 and command_args.count('auth') != 0:
            if not LoginManagerMixin().authenticate(id=self.__send_id):
                raise AuthError('Вы не авторизованны!')
            return_data.append(True)

        if text_in_msg.find(command) != -1 and command_args.count('admin') != 0 and self.__send_id in self.admins:
            return_data.append(command)

        if text_in_msg.find(command) != -1 and command_args.count('args'):
            return_data.append(command)
        return return_data
