import logging

from django.core.management import BaseCommand

from bot.models import TgUser
from bot.tg.client import TgClient
from bot.tg.schemas import Message
from goals.models import Goal, GoalCategory

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Класс слушателя сообщений для бота.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.offset = 0
        self.tg_client = TgClient()

    def handle(self, *args, **options):
        """
        Получение сообщений для бота и их передача в обработчик.
        Args:
             *args
             **options
        Returns:
            None
        """
        logger.info('Bot starts handling')
        while True:
            res = self.tg_client.get_updates(offset=self.offset)
            for item in res.result:
                self.offset = item.update_id + 1
                self.handle_message(item.message)
                # logger.info(item.message)

    def handle_message(self, msg: Message) -> None:
        """
        Роутер сообщений. Выполняет проверку, что пользователь есть в базе данных.
        Если пользователя нет в базе, то создание TgUser и ожидание подтверждение кодом в веб-интерфейсе.
        Если TgUser найден и привязан к пользователю - пользователь аутентифицирован.
        Args:
            msg: объект Message - сообщение
        Returns:
            None
        """
        # if not hasattr(msg, 'chat'):
        #     return

        tg_user, created = TgUser.objects.get_or_create(chat_id=msg.chat.id)

        if created:
            self.tg_client.send_message(msg.chat.id, '[greeting]')
        if tg_user.user:
            self.handle_authorized(tg_user, msg)
        else:
            self.handle_unauthorized(tg_user, msg)

    def handle_unauthorized(self, tg_user: TgUser, msg: Message) -> None:
        """
        Обработчик для неаутентифицированных пользователей.
        Если TgUser найден, но не привязан к пользователю системы, то отправляем новый код верификации.
        Args:
            tg_user: объект TgUser - пользователь
            msg: объект Message - сообщение
        Returns:
            None
        """
        code = tg_user.set_verification_code()
        self.tg_client.send_message(tg_user.chat_id, f'[verification code] {code}')

    def handle_authorized(self, tg_user: TgUser, msg: Message) -> None:
        """
        Обработчик для утентифицированных пользователей. Основной обработчик команд.
        Распознает команду и вызывает нужный обработчик.
        Args:
            tg_user: объект TgUser - пользователь
            msg: объект Message - сообщение
        Returns:
            None
        """
        if msg.text == '/goals':
            self.fetch_goals(tg_user, msg)
        elif msg.text == '/create':
            self.choice_category(tg_user, msg)
        elif msg.text.startswith('/'):
            self.tg_client.send_message(msg.chat.id, '[unknown command]')
            self.tg_client.send_message(msg.chat.id, '[input /goals or /create command]')
        else:
            self.tg_client.send_message(msg.chat.id, '[input /goals or /create command]')

    def fetch_goals(self, tg_user: TgUser, msg: Message) -> None:
        """
        Отправка всех целей пользователя в telegram.
        Если целей у пользователя нет, то отправить сообщение, что целей нет.
        Args:
            tg_user: объект TgUser - пользователь
            msg: объект Message - сообщение
        Returns:
            None
        """
        goals = Goal.objects.filter(
            category__board__participants__user_id=tg_user.user.id,
            category__is_deleted=False,
        ).exclude(
            status=Goal.Status.archived
        )
        if goals:
            response_list = [f'- {goal.title} (category: {goal.category}, '
                             f'priority: {goal.Priority.choices[goal.priority - 1][1]}, '
                             f'deadline: {goal.due_date.strftime("%Y-%m-%d") if goal.due_date else "not set"}'
                             for goal in goals]
            self.tg_client.send_message(msg.chat.id, '\n'.join(response_list))
        else:
            self.tg_client.send_message(msg.chat.id, '[goals list is empty]')

    def choice_category(self, tg_user: TgUser, msg: Message) -> None:
        """
        Метод возвращает все категории пользователя в telegram и просит выбрать категорию, в для создания новой цели.
        Args:
            tg_user: объект TgUser - пользователь
            msg: объект Message - сообщение
        Returns:
            None
        """
        categories = GoalCategory.objects.filter(
            board__participants__user_id=tg_user.user.id,
            is_deleted=False
        )

        if not categories:
            self.tg_client.send_message(msg.chat.id, '[you have no categories]')
            return None

        dict_categories = {cat.title: cat for cat in categories}
        response_list = [f'{cat.title}' for cat in categories]
        self.tg_client.send_message(
            msg.chat.id,
            '[select category or send /cancel to cancel]\n' + '\n'.join(response_list)
        )

        flag = True
        while flag:
            response = self.tg_client.get_updates(offset=self.offset)
            for item in response.result:
                self.offset = item.update_id + 1

                if item.message.text in dict_categories:
                    category = dict_categories.get(item.message.text)
                    self.create_goal(tg_user, msg, category)
                    flag = False
                elif item.message.text == '/cancel':
                    self.tg_client.send_message(msg.chat.id, '[operation was canceled]')
                    flag = False
                else:
                    self.tg_client.send_message(msg.chat.id, '[category is not exist]')

    def create_goal(self, tg_user: TgUser, msg: Message, category: GoalCategory) -> None:
        """
        Метод создания новой цели в выбранной категории
        Args:
            tg_user: объект TgUser - пользователь
            msg: объект Message - сообщение
            category: GoalCategory - выбранная категория
        Returns:
            None
        """
        self.tg_client.send_message(msg.chat.id, text='[input title of new goal]')

        flag = True
        while flag:
            response = self.tg_client.get_updates(offset=self.offset)
            for item in response.result:
                self.offset = item.update_id + 1

                if item.message.text == '/cancel':
                    self.tg_client.send_message(msg.chat.id, '[operation was canceled]')
                    flag = False
                else:
                    goal = Goal.objects.create(category=category, user=tg_user.user, title=item.message.text)
                    self.tg_client.send_message(
                        msg.chat.id,
                        f'[goal was created successfully ({goal.title} in {goal.category})]'
                    )
                    flag = False
