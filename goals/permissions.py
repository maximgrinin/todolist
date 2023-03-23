from rest_framework import permissions

from goals.models import (Board, BoardParticipant, Goal, GoalCategory,
                          GoalComment)


class BoardPermissions(permissions.IsAuthenticated):
    """
    Наследование от permissions.IsAuthenticated позволяет проверить, что пользователь аутентифицирован. Класс добавляет
    фильтр по разрешенным ролям пользователя, если request.method не равен GET. Изменять/удалять доску имеет право
    только создатель доски.
    """
    def has_object_permission(self, request, view, obj: Board) -> bool:
        _filters: dict = {'user_id': request.user.id, 'board_id': obj.id}

        if request.method not in permissions.SAFE_METHODS:
            _filters['role'] = BoardParticipant.Role.owner

        return BoardParticipant.objects.filter(**_filters).exists()


class GoalCategoryPermissions(permissions.IsAuthenticated):
    """
    Наследование от permissions.IsAuthenticated позволяет проверить, что пользователь аутентифицирован. Класс добавляет
    фильтр по разрешенным ролям пользователя, если request.method не равен GET.
    Менять/удалять категорию имеет право создатель доски или редактор.
    """
    def has_object_permission(self, request, view, obj: GoalCategory) -> bool:
        _filters: dict = {'user_id': request.user.id, 'board_id': obj.board_id}

        if request.method not in permissions.SAFE_METHODS:
            _filters['role__in'] = [BoardParticipant.Role.owner, BoardParticipant.Role.writer]

        return BoardParticipant.objects.filter(**_filters).exists()


class GoalPermissions(permissions.IsAuthenticated):
    """
    Наследование от permissions.IsAuthenticated позволяет проверить, что пользователь аутентифицирован. Класс добавляет
    фильтр по разрешенным ролям пользователя, если request.method не равен GET. Менять/удалять цель имеет право
    создатель доски или редактор.
    """
    def has_object_permission(self, request, view, obj: Goal) -> bool:
        _filters: dict = {'user_id': request.user.id, 'board_id': obj.category.board_id}

        if request.method not in permissions.SAFE_METHODS:
            _filters['role__in'] = [BoardParticipant.Role.owner, BoardParticipant.Role.writer]

        return BoardParticipant.objects.filter(**_filters).exists()


class GoalCommentPermissions(permissions.IsAuthenticated):
    """
    Наследование от permissions.IsAuthenticated позволяет проверить, что пользователь аутентифицирован. Пользователь
    может создавать комментарии к целям, в досках которых он имеет роль "владелец" или "редактор". Пользователь не может
    редактировать или удалять чужие комментарии.
    """
    def has_object_permission(self, request, view, obj: GoalComment) -> bool:
        return any((
            request.method in permissions.SAFE_METHODS,
            obj.user.id == request.user.id
        ))
