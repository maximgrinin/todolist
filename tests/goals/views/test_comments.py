import pytest
from django.urls import reverse
from rest_framework import status

from goals.models import Goal, GoalCategory, GoalComment
from tests.utils import BaseTestCase


@pytest.mark.django_db()
class TestCreateCommentView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, goal_factory, goal_category_factory, user):
        self.url = reverse('goals:create-comment')
        self.board = board_factory.create(with_owner=user)
        self.cat: GoalCategory = goal_category_factory.create(board=self.board, user=user)
        self.goal: Goal = goal_factory.create(user=user, category=self.cat)

    def test_auth_required(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_success(self, auth_client, settings):
        response = auth_client.post(self.url, data={
            'text': 'test comment', 'goal': self.goal.pk,
        })

        assert response.status_code == status.HTTP_201_CREATED
        new_comment = GoalComment.objects.last()
        assert response.json() == {
            'id': response.data.get('id'),
            'created': self.datetime_to_str(new_comment.created),
            'updated': self.datetime_to_str(new_comment.updated),
            'text': 'test comment',
            'goal': self.goal.pk
        }


@pytest.mark.django_db()
class TestCommentyListView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, goal_factory, goal_category_factory, user):
        self.url = reverse('goals:list-comment')
        # self.board = board_factory.create(with_owner=user)
        # self.cat: GoalCategory = goal_category_factory.create(board=self.board, user=user)
        # self.goal: Goal = goal_factory.create(user=user, category=self.cat)
        # self.goals = goal_factory.create_batch(5, user=user, category=self.cat)

    def test_auth_required(self, client):
        response = client.get(self.url, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list(self, auth_client, settings):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db()
class TestRetrieveCommentView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, goal_factory, goal_category_factory, goal_comment_factory, user):
        self.board = board_factory.create(with_owner=user)
        self.cat: GoalCategory = goal_category_factory.create(board=self.board, user=user)
        self.goal: Goal = goal_factory.create(user=user, category=self.cat)
        self.comment: GoalComment = goal_comment_factory.create(goal=self.goal, user=user)
        self.url = reverse('goals:comment', args=[self.comment.id])

    def test_auth_required(self, client):
        response = client.get(self.url, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve(self, auth_client, user):
        response = auth_client.get(self.url, {})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'id': response.data.get('id'),
                                   'user': {'id': user.pk,
                                            'username': user.username,
                                            'first_name': '',
                                            'last_name': '',
                                            'email': user.email},
                                   'created': self.datetime_to_str(self.comment.created),
                                   'updated': self.datetime_to_str(self.comment.updated),
                                   'text': self.comment.text,
                                   'goal': self.goal.pk}

    def test_update(self, auth_client):
        response = auth_client.put(self.url, data={'text': 'test text update'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('text') == 'test text update'

    def test_delete(self, auth_client):
        response = auth_client.delete(self.url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
