import sys
import datetime
import time
from threading import Thread

from vk_api.bot_longpoll import VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard

from .core.utils import BaseStarter, LoginManagerMixin, APIBackendMixin, KeyboardMixin, FileDB, BotLogger


class VkBot(BaseStarter):
    """
    A class that has collected all the basic elements for creating a fully functional bot
    (Launching, working with an account, working with an external API, working with a keyboard).
    Implemented basic commands needed in most bots
    """

    logger = BotLogger().get_logger()

    def __init__(self, system_name: str = '[Автоматическое оповещение]', *args, **kwargs):
        self.system_name = system_name
        self.standart_msg_block = ''
        self.api = APIBackendMixin()
        self.keyboard = KeyboardMixin()
        self.user = LoginManagerMixin()
        if kwargs.get('logger'):
            self.logger = kwargs.get('logger')
        super().__init__(*args, **kwargs)

    @logger.catch
    def send_msg(self, send_id: int, message: str, keyboard: VkKeyboard = None) -> bool:
        """ Sending a message """
        if keyboard:
            self._vk_api.messages.send(peer_id=send_id,
                                       message=message,
                                       random_id=get_random_id(),
                                       keyboard=keyboard.get_keyboard())
        else:
            self._vk_api.messages.send(peer_id=send_id,
                                       message=message,
                                       random_id=get_random_id())
        return True

    @logger.catch
    def get_user_name(self, user_id: int) -> str:
        """ Getting the username """
        return self._vk_api.users.get(user_id=user_id)[0]['first_name']

    @logger.catch
    def get_user_last_name(self, user_id: int) -> str:
        """ Get the user's last name """
        return self._vk_api.users.get(user_id=user_id)[0]['last_name']

    @logger.catch
    def get_full_name(self, send_id: int) -> str:
        return '{} {}'.format(self.get_user_name(send_id), self.get_user_last_name(send_id))

    @logger.catch
    def get_user_closed(self, send_id: int) -> str:
        print(self._vk_api.users.get(user_id=send_id)[0]['is_closed'])

    @logger.catch
    def get_bot_info(self, *args, **kwargs):
        time_format = str(datetime.timedelta(seconds=time.time() - self.__start_time))
        bot_info = 'Бот работает: {}.\nВыполнено: {} команд'.format(time_format, self.__executed_commands)
        print(bot_info)

    @logger.catch
    def send_admin_msg(self, msg):
        for admin in self.admins:
            self.send_msg(admin, message=msg)

    @logger.catch
    def command_help(self, send_id: int) -> None:
        message = ''
        for command in self.commands:
            command_not_param = command.split(' *')[0]
            if not command.count('*nshow'):
                if command.count('*admin'):
                    if send_id in self.admins:
                        message += f"{command_not_param}: {self.commands[command]['comment']}  😎\n\n"
                else:
                    message += command_not_param + ': ' + self.commands[command]['comment'] + '\n\n'
        self.send_msg(send_id, message=message, keyboard=self.keyboard.get_standart_keyboard())

    @logger.catch
    def command_msg(self, send_id: int):
        text_in_msg = self._text_in_msg.replace(self._command_args, '')
        user_id = text_in_msg.split()[1]
        msg = ' '.join(text_in_msg.split()[2:])
        username = FileDB().get_by_value(value=user_id, index=0)
        username = username[0][1]

        self.send_msg(user_id,
                      message=f'{self.system_name}{msg}',
                      )

        self.send_msg(send_id,
                      message=f'✅️ Сообщение пользователю: {username} - успешно отправлено!',
                      )

    @logger.catch
    def command_killbot(self, send_id: int):
        if send_id in self.admins:
            login = self.user.authenticate(str(send_id))[1]
            self.send_admin_msg(f'😈Бот успешно остановлен, Администратором {login}!')
            sys.exit()

    @logger.catch
    def start(self, commands: dict, debug: bool = None, multithread: bool = True) -> None:
        """ Запуск бота """
        print('Я запущен!')

        self.__start_time = time.time()
        self.__executed_commands = 0

        if (self.debug != debug) and (debug is not None):
            self.debug = debug

        self.commands = commands
        for event in self._long_poll.listen():  # Слушаем сервер
            # Пришло новое сообщение
            if event.type == VkBotEventType.MESSAGE_NEW:
                send_id = event.object.peer_id
                if self.debug and send_id in self.admins:
                    if multithread:
                        thread = Thread(target=self._command_starter, args=[event])
                        thread.start()
                    else:
                        self._command_starter(event=event)
                    self.__executed_commands += 1
                else:
                    try:
                        if multithread:
                            thread = Thread(target=self._command_starter, args=[event])
                            thread.start()
                        else:
                            self._command_starter(event=event)
                        self.__executed_commands += 1
                    except Exception as exc:
                        text_message = event.object.text
                        username = '\n👤Имя пользователя: {}\n📝Текст сообщения: {}'.format(self.get_full_name(send_id),
                                                                                            text_message)
                        self.__error_handler(exc=exc, any=username)
                        self.send_msg(send_id,
                                      message='🆘На сервере произошла ошибка🆘\nМы уже оповестили Администрацию об этом, приносим свои извинения💌',
                                      keyboard=self.keyboard.get_standart_keyboard())

    @logger.catch
    def get_command_text(self, command, command_args):
        return ''.join(list(command.replace(command_args, ''))[1:]).lstrip()

    @logger.catch
    def __error_handler(self, exc, any: str = ''):
        self.send_admin_msg(f'❌Произошла ошибка: {exc}\n{any}')
