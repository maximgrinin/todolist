from django.db import transaction
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from goals.filters import GoalDateFilter
from goals.models import (Board, BoardParticipant, Goal, GoalCategory,
                          GoalComment)
from goals.permissions import (BoardPermissions, GoalCategoryPermissions,
                               GoalCommentPermissions, GoalPermissions)
from goals.serializers import (BoardCreateSerializer, BoardListSerializer,
                               BoardSerializer, GoalCategoryCreateSerializer,
                               GoalCategorySerializer,
                               GoalCommentCreateSerializer,
                               GoalCommentSerializer, GoalCreateSerializer,
                               GoalSerializer)


class BoardCreateView(generics.CreateAPIView):
    """
    Позволяет пользователю со статусом IsAuthenticated создать доску и получить в ней роль "владелец".
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoardCreateSerializer

    def perform_create(self, serializer):
        BoardParticipant.objects.create(user=self.request.user, board=serializer.save())


class BoardListView(generics.ListAPIView):
    """
    Позволяет пользователю с разрешениями BoardPermissions видеть список своих досок и досок, в которых он является
    участником.
    """
    model = Board
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoardListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['title']

    def get_queryset(self):
        # return Board.objects.prefetch_related('participants').filter(
        return Board.objects.filter(
            participants__user_id=self.request.user.id,
            is_deleted=False
        )


class BoardView(generics.RetrieveUpdateDestroyAPIView):
    """
    Позволяет пользователю с разрешениями BoardPermissions видеть информацию по созданным пользователем доскам и доскам,
    в которых пользователь является участником. Пользователь с ролью "владелец" может обновлять или удалять доску. При
    удалении доски она получает признак is_deleted, присвоенные доске категории получают статус Архив, цели получают
    статус Архив, но не удаляются из БД.
    """
    model = Board
    permission_classes = [BoardPermissions]
    serializer_class = BoardSerializer

    def get_queryset(self):
        # Обратите внимание на фильтрацию – она идет через participants
        # return Board.objects.filter(participants__user=self.request.user, is_deleted=False)
        return Board.objects.filter(is_deleted=False)

    def perform_destroy(self, instance: Board) -> Board:
        # При удалении доски помечаем ее как is_deleted,
        # «удаляем» категории, обновляем статус целей
        with transaction.atomic():
            instance.is_deleted = True
            instance.save(update_fields=('is_deleted',))
            instance.categories.update(is_deleted=True)
            Goal.objects.filter(category__board=instance).update(status=Goal.Status.archived)
        return instance


class GoalCategoryCreateView(generics.CreateAPIView):
    """
    Позволяет создать категорию пользователю с разрешениями GoalCategoryPermissions.
    """
    # permission_classes = [GoalCategoryPermissions]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GoalCategoryCreateSerializer


class GoalCategoryListView(generics.ListAPIView):
    """
    Позволяет пользователю с разрешениями GoalCategoryPermissions видеть информацию по категориям, в досках, которых он
    является участником и созданным им самим категории.
    """
    permission_classes = [GoalCategoryPermissions]
    serializer_class = GoalCategorySerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title', 'description']

    def get_queryset(self):
        # return GoalCategory.objects.prefetch_related('board__participants').filter(
        return GoalCategory.objects.filter(
            board__participants__user_id=self.request.user.id,
            is_deleted=False
        )


class GoalCategoryView(generics.RetrieveUpdateDestroyAPIView):
    """
    Позволяет пользователю с разрешениями GoalCategoryPermissions видеть информацию по категориям, в досках, которых он
    является участником и созданным им самим категориям. Пользователь может обновлять или удалять категорию в
    зависимости от ролей доступа и ролей участия в доске. При удалении категории все цели этой категории переходят в
    статус Архив и не отображаются в списке целей, однако остаются в БД.
    """
    serializer_class = GoalCategorySerializer
    permission_classes = [GoalCategoryPermissions]

    def get_queryset(self):
        # return GoalCategory.objects.prefetch_related('board__participants').filter(
        return GoalCategory.objects.filter(
            board__participants__user_id=self.request.user.id,
            is_deleted=False
        )

    def perform_destroy(self, instance: GoalCategory) -> GoalCategory:
        with transaction.atomic():
            instance.is_deleted = True
            instance.save(update_fields=('is_deleted',))
            instance.goals.update(status=Goal.Status.archived)
        return instance


class GoalCreateView(generics.CreateAPIView):
    """
    Позволяет пользователю с разрешениями GoalPermissions создать цель.
    """
    serializer_class = GoalCreateSerializer
    permission_classes = [GoalPermissions]


class GoalListView(generics.ListAPIView):
    """
    Позволяет пользователю с разрешениями GoalPermissions видеть список целей, в досках, которых он является участником,
    а также созданные им самим цели.
    """
    permission_classes = [GoalPermissions]
    serializer_class = GoalSerializer
    filterset_class = GoalDateFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title', 'description']

    def get_queryset(self) -> QuerySet[Goal]:
        return Goal.objects.filter(
            category__board__participants__user_id=self.request.user.id,
            category__is_deleted=False
        ).exclude(
            status=Goal.Status.archived
        )


class GoalView(generics.RetrieveUpdateDestroyAPIView):
    """
    Позволяет пользователю с разрешениями GoalPermissions видеть информацию по созданным им самим целям, а также целям
    в досках, в которых он является участником. Пользователь может обновлять или удалять цель в зависимости от ролей
    доступа и ролей участия в доске. Цель не отображается, если присвоенная ей категория имеет статус Архив. При
    удалении категории все цели этой категории переходят в статус Архив и не отображаются, однако остаются в БД.
    """
    permission_classes = [GoalPermissions]
    serializer_class = GoalSerializer

    def get_queryset(self) -> QuerySet[Goal]:
        return Goal.objects.filter(
            category__board__participants__user_id=self.request.user.id,
            category__is_deleted=False,
        ).exclude(
            status=Goal.Status.archived
        )

    def perform_destroy(self, instance: Goal) -> Goal:
        instance.status = Goal.Status.archived
        instance.save(update_fields=('status',))
        return instance


class GoalCommentCreateView(generics.CreateAPIView):
    """
    Позволяет пользователю с разрешениями GoalCommentPermissions создать комментарий к цели.
    """
    serializer_class = GoalCommentCreateSerializer
    permission_classes = [GoalCommentPermissions]


class GoalCommentListView(generics.ListAPIView):
    """
    Позволяет пользователю с разрешениями GoalCommentPermissions видеть список своих комментариев и комментарии к целям,
    в досках, в которых он является участником.
    """
    model = GoalComment
    permission_classes = [GoalCommentPermissions]
    serializer_class = GoalCommentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['goal']
    ordering = ['-created']

    def get_queryset(self):
        # return GoalComment.objects.filter(user_id=self.request.user.id)
        return GoalComment.objects.filter(
            goal__category__board__participants__user_id=self.request.user.id,
        )


class GoalCommentView(generics.RetrieveUpdateDestroyAPIView):
    """
    Позволяет пользователю с разрешениями GoalCommentPermissions видеть информацию по созданным пользователем
    комментариям к целям, в т.ч. в досках которых он является участником. Пользователь может обновлять и удалять
    комментарий в зависимости от ролей доступа и ролей участия в доске. Комментарии удаляются полностью при удалении
    Пользователя или Цели.
    """
    model = GoalComment
    permission_classes = [GoalCommentPermissions]
    serializer_class = GoalCommentSerializer

    def get_queryset(self):
        return GoalComment.objects.filter(
            user_id=self.request.user.id
        )
