from rest_framework import permissions

from goals.models import BoardParticipant


class IsOwnerOrReadOnly(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user_id == request.user.id


class BoardPermissions(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        _filters: dict = {'user': request.user, 'board': obj}

        if request.method not in permissions.SAFE_METHODS:
            _filters['role'] = BoardParticipant.Role.owner

        return BoardParticipant.objects.filter(_filters).exists()
