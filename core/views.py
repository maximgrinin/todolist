from typing import Any

from django.contrib.auth import login, logout
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from core.models import User
from core.serializers import (CreateUserSerializer, LoginSerializer,
                              ProfileSerializer, UpdatePasswordSerializer)


class SignUpView(generics.CreateAPIView):
    serializer_class: Serializer = CreateUserSerializer


class LoginView(generics.CreateAPIView):
    serializer_class: Serializer = LoginSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        login(request=request, user=serializer.save())
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class: Serializer = ProfileSerializer
    permission_classes: tuple[permissions.BasePermission, ...] = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance: User):
        logout(self.request)


class UpdatePasswordView(generics.UpdateAPIView):
    serializer_class: Serializer = UpdatePasswordSerializer
    permission_classes: tuple[permissions.BasePermission, ...] = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user
