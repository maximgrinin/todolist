import pytest
from django.urls import reverse
from rest_framework import status

from goals.models import Goal, GoalCategory
from tests.utils import BaseTestCase


@pytest.mark.django_db()
class TestCreateGoalView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, goal_factory, goal_category_factory, user):
        self.url = reverse('goals:create-goal')
        self.board = board_factory.create(with_owner=user)
        self.cat: GoalCategory = goal_category_factory.create(board=self.board, user=user)

    def test_auth_required(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_success(self, auth_client, settings, user):
        response = auth_client.post(self.url, data={
            'title': 'test title', 'category': self.cat.pk, 'user': user,
        })

        assert response.status_code == status.HTTP_201_CREATED
        new_goal = Goal.objects.last()
        assert response.json() == {
            'id': new_goal.id,
            'title': new_goal.title,
            'category': new_goal.category.id,
            'description': new_goal.description,
            'due_date': new_goal.due_date,
            'priority': new_goal.priority,
            'status': new_goal.status,
            'created': self.datetime_to_str(new_goal.created),
            'updated': self.datetime_to_str(new_goal.updated),
        }


@pytest.mark.django_db()
class TestGoalListView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, goal_factory, goal_category_factory, user):
        self.url = reverse('goals:list-goals')
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
class TestRetrieveGoalView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, goal_factory, goal_category_factory, user):
        self.board = board_factory.create(with_owner=user)
        self.cat: GoalCategory = goal_category_factory.create(board=self.board, user=user)
        self.goal: Goal = goal_factory.create(user=user, category=self.cat)
        self.url = reverse('goals:goal', args=[self.goal.id])

    def test_auth_required(self, client):
        response = client.get(self.url, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve(self, auth_client, user):
        response = auth_client.get(self.url, {})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': response.data.get('id'),
            'title': self.goal.title,
            'category': self.goal.category.id,
            'description': self.goal.description,
            'due_date': self.goal.due_date,
            'priority': self.goal.priority.value,
            'status': self.goal.status.value,
            'user': user.pk,
            'created': self.datetime_to_str(self.goal.created),
            'updated': self.datetime_to_str(self.goal.updated),
        }

    def test_update(self, auth_client):
        response = auth_client.put(self.url, data={'title': 'test title update', 'category': self.cat.pk})

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('title') == 'test title update'

    def test_delete(self, auth_client):
        response = auth_client.delete(self.url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
