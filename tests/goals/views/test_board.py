import pytest
from django.urls import reverse
from rest_framework import status

from goals.models import BoardParticipant, Goal, GoalCategory
from tests.utils import BaseTestCase


@pytest.fixture()
def another_user(user_factory):
    return user_factory.create()


@pytest.mark.django_db()
class TestRetrieveBoardView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, user):
        self.board = board_factory.create(with_owner=user)
        self.url = reverse('goals:retrieve-update-destroy-boards', args=[self.board.id])

    def test_auth_required(self, client):
        response = client.get(self.url, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_not_board_participant(self, client, another_user):
        assert not self.board.participants.filter(user=another_user).count()

        client.force_login(another_user)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_success(self, auth_client, user):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        assert self.board.participants.count() == 1
        participant: BoardParticipant = self.board.participants.last()
        assert participant.user == user

        assert response.json() == {  # noqa: ECE001
            'id': self.board.id,
            'participants': [
                {
                    'id': participant.id,
                    'role': BoardParticipant.Role.owner.value,
                    'user': user.username,
                    'created': self.datetime_to_str(participant.created),
                    'updated': self.datetime_to_str(participant.created),
                    'board': participant.board_id
                }
            ],
            'created': self.datetime_to_str(self.board.created),
            'updated': self.datetime_to_str(self.board.updated),
            'title': self.board.title,
            'is_deleted': False
        }


@pytest.mark.django_db()
class TestDestroyBoardView(BaseTestCase):

    @pytest.fixture(autouse=True)
    def setup(self, board_factory, goal_category_factory, goal_factory, user):  # noqa: PT004
        self.board = board_factory.create(with_owner=user)
        self.url = reverse('goals:retrieve-update-destroy-boards', args=[self.board.id])
        self.cat: GoalCategory = goal_category_factory.create(board=self.board, user=user)
        self.goal: Goal = goal_factory.create(category=self.cat, user=user)
        self.participant: BoardParticipant = self.board.participants.last()

    def test_user_not_board_participant(self, client, another_user):
        assert not self.board.participants.filter(user=another_user).count()

        client.force_login(another_user)
        response = client.delete(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_success(self, auth_client):
        assert self.participant.role == BoardParticipant.Role.owner

        response = auth_client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        self.board.refresh_from_db(fields=('is_deleted',))
        self.cat.refresh_from_db(fields=('is_deleted',))
        self.goal.refresh_from_db(fields=('status',))
        assert self.board.is_deleted
        assert self.cat.is_deleted
        assert self.goal.status == Goal.Status.archived


@pytest.mark.django_db()
class TestUpdateBoardView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, user):  # noqa: PT004
        self.board = board_factory.create(with_owner=user)
        self.url = reverse('goals:retrieve-update-destroy-boards', args=[self.board.id])
        self.participant: BoardParticipant = self.board.participants.last()

    @pytest.mark.parametrize('method', ['put', 'patch'])
    def test_auth_required(self, client, method):
        response = getattr(client, method)(self.url, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('method', ['put', 'patch'])
    def test_user_not_board_participant(self, client, another_user, method):
        assert not self.board.participants.filter(user=another_user).count()

        client.force_login(another_user)
        response = getattr(client, method)(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_title_by_owner(self, auth_client, faker):
        assert self.participant.role == BoardParticipant.Role.owner
        new_title = faker.sentence()

        response = auth_client.patch(self.url, {'title': new_title})
        assert response.status_code == status.HTTP_200_OK

        self.board.refresh_from_db(fields=('title',))
        assert self.board.title == new_title

    def test_delete_participant_from_board(self, auth_client, another_user):
        BoardParticipant.objects.create(
            board=self.board,
            user=another_user,
            role=BoardParticipant.Role.writer
        )

        response = auth_client.patch(self.url, {'participants': []})

        assert response.status_code == status.HTTP_200_OK
        assert BoardParticipant.objects.count() == 1
