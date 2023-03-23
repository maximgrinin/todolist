from datetime import datetime

from rest_framework.fields import DateTimeField


class BaseTestCase:
    @staticmethod
    def datetime_to_str(date_time: datetime) -> str:
        return DateTimeField().to_representation(date_time)
