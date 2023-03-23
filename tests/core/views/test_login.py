import pytest
from django.urls import reverse
from rest_framework import status

from tests.utils import BaseTestCase


@pytest.mark.django_db()
class TestLoginView(BaseTestCase):
    url = reverse('core:login')

    def test_user_not_found(self, client, user_factory):
        user = user_factory.build()

        response = client.post(self.url, data={
            'username': user.username,
            'password': user.password,
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_credentials(self, client, user, faker):
        response = client.post(self.url, data={
            'username': user.username,
            'password': faker.password(),
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(('is_active', 'status_code'), [
        (True, status.HTTP_200_OK),
        (False, status.HTTP_403_FORBIDDEN),
    ], ids=['active', 'inactive'])
    def test_inactive_user_login_denied(self, client, user_factory, faker, is_active, status_code):
        password = faker.password()
        user = user_factory.create(password=password, is_active=is_active)

        response = client.post(self.url, data={
            'username': user.username,
            'password': password,
        })

        assert response.status_code == status_code

    def test_success(self, client, faker, user_factory):
        password = faker.password()
        user = user_factory.create(password=password)

        response = client.post(self.url, data={
            'username': user.username,
            'password': password,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username
        }
