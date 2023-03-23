import pytest
from django.urls import reverse
from rest_framework import status

from tests.utils import BaseTestCase


@pytest.mark.django_db()
class TestBoardListView(BaseTestCase):
    url = reverse('goals:list-boards')

    def test_auth_required(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_not_board_participant(self, auth_client, board, user, board_factory):
        assert not board.participants.count()
        another_board = board_factory.create(with_owner=user)
        assert another_board.participants.count() == 1

        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'id': another_board.id,
                'created': self.datetime_to_str(another_board.created),
                'updated': self.datetime_to_str(another_board.updated),
                'title': another_board.title,
                'is_deleted': False
            }
        ]
