import pytest
from django.urls import reverse
from rest_framework import status

from goals.models import GoalCategory
from tests.utils import BaseTestCase


@pytest.mark.django_db()
class TestCreateCategoryView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, goal_category_factory, user):
        self.url = reverse('goals:create-category')
        self.board = board_factory.create(with_owner=user)
        self.cat: GoalCategory = goal_category_factory.create(board=self.board, user=user)

    def test_auth_required(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_success(self, auth_client, settings):
        response = auth_client.post(self.url, data={
            'title': 'Category Title', 'board': self.board.pk,
        })

        assert response.status_code == status.HTTP_201_CREATED
        new_category = GoalCategory.objects.last()
        assert response.json() == {
            'id': new_category.id,
            'created': self.datetime_to_str(new_category.created),
            'updated': self.datetime_to_str(new_category.updated),
            'title': 'Category Title',
            'board': self.board.pk,
            'is_deleted': False
        }


@pytest.mark.django_db()
class TestCategoryListView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, goal_category_factory, user):
        self.url = reverse('goals:list-categories')
        # self.board = board_factory.create(with_owner=user)
        # self.cats: GoalCategory = goal_category_factory.create_batch(5, board=self.board, user=user)

    def test_auth_required(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list(self, auth_client, settings):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db()
class TestRetrieveCategoryView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, goal_category_factory, user):
        self.board = board_factory.create(with_owner=user)
        self.cat: GoalCategory = goal_category_factory.create(board=self.board, user=user)
        self.url = reverse('goals:category', args=[self.cat.id])

    def test_auth_required(self, client):
        response = client.get(self.url, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve(self, auth_client, user):
        response = auth_client.get(self.url)

        expected_response = {'id': self.cat.id,
                             'user': {'id': user.pk,
                                      'username': user.username,
                                      'first_name': '',
                                      'last_name': '',
                                      'email': user.email},
                             'created': response.data.get('created'),
                             'updated': response.data.get('updated'),
                             'title': self.cat.title,
                             'board': self.board.pk
                             }

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_response

    def test_update(self, auth_client):
        response = auth_client.put(self.url, data={'board': self.board.pk, 'title': 'test name category'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('title') == 'test name category'

    def test_delete(self, auth_client):
        response = auth_client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
