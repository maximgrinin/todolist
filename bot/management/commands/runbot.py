import logging

from django.core.management import BaseCommand

from bot.models import TgUser
from bot.tg.client import TgClient
from bot.tg.schemas import Message

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tg_client = TgClient()

    def handle(self, *args, **options):
        offset = 0
        # print('Bot starts handling')
        logger.info('Bot starts handling')
        while True:
            res = self.tg_client.get_updates(offset=offset)
            for item in res.result:
                offset = item.update_id + 1
                self.handle_message(item.message)
                # print(item.message)
                # logger.info(item.message)

    def handle_message(self, msg: Message):
        # self.tg_client.send_message(chat_id=msg.chat.id, text=msg.text)
        tg_user, created = TgUser.objects.get_or_create(chat_id=msg.chat.id)

        if tg_user.user:
            self.handle_authorized(tg_user, msg)
        else:
            self.handle_unauthorized(tg_user, msg)

    def handle_unauthorized(self, tg_user: TgUser, msg: Message):
        self.tg_client.send_message(msg.chat.id, 'Hello!')

        code = tg_user.set_verification_code()
        self.tg_client.send_message(tg_user.chat_id, f'Your verification code is: {code}')

    def handle_authorized(self, tg_user: TgUser, msg: Message):
        logger.info('Authorized')
