import os

from django.db import models

from core.models import User


class TgUser(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, null=True, blank=True, default=None)
    verification_code = models.CharField(max_length=50, null=True, blank=True, default=None)

    def _generate_verification_code(self) -> str:
        return os.urandom(12).hex()

    def set_verification_code(self) -> str:
        code = self._generate_verification_code()
        self.verification_code = code
        self.save(update_fields=('verification_code',))
        return code

    def __str__(self):
        return f'{self.user} at {self.chat_id}'

    class Meta:
        verbose_name = 'Telegram-пользователь'
        verbose_name_plural = 'Telegram-пользователи'
