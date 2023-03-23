from django.db import transaction
from rest_framework import exceptions, serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.models import User
from core.serializers import ProfileSerializer
from goals.models import (Board, BoardParticipant, Goal, GoalCategory,
                          GoalComment)


class GoalCategoryCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Категории создает категорию, учитывая права и роли текущего пользователя.
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = GoalCategory
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user', 'is_deleted')

    def validate_board(self, value: Board) -> Board:
        if value.is_deleted:
            raise serializers.ValidationError('Board is deleted')

        if not BoardParticipant.objects.filter(
                board=value,
                role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
                user_id=self.context['request'].user.id
        ):
            raise PermissionDenied
        return value


class GoalCategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для Категории выводит информацию по категории или списку категорий.
    """
    user = ProfileSerializer(read_only=True)

    class Meta:
        model = GoalCategory
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user', 'board')
        # read_only_fields = ('id', 'created', 'updated', 'user')
        extra_kwargs = {
            'is_deleted': {'write_only': True}
        }


class GoalCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Цели создает цель, учитывая права и роли текущего пользователя.
    """
    category = serializers.PrimaryKeyRelatedField(
        queryset=GoalCategory.objects.filter(is_deleted=False)
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user')

    def validate_category(self, value: GoalCategory) -> GoalCategory:
        if self.context['request'].user != value.user:
            raise exceptions.PermissionDenied
        return value

    # def validate_category(self, value: GoalCategory):
    #     if not BoardParticipant.objects.filter(
    #             board_id=value.board_id,
    #             role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
    #             user_id=self.context['request'].user.id
    #     ):
    #         raise PermissionDenied
    #     return value


class GoalSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Цели выводит информацию по цели или списку целей.
    """
    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user')

    def validate_category(self, value: GoalCategory) -> GoalCategory:
        if self.context['request'].user.id != value.user_id:
            raise exceptions.PermissionDenied
        return value


class GoalCommentCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Комментария создает комментарий к цели, учитывая права и роли текущего пользователя.
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = GoalComment
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user')

    def validate_goal(self, value: Goal) -> Goal:
        if value.status == Goal.Status.archived:
            raise ValidationError('Goal not found')
        if not BoardParticipant.objects.filter(
            board_id=value.category.board.id,
            role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
            user_id=self.context['request'].user.id
        ).exists():
            raise PermissionDenied
        return value


class GoalCommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Комментария выводит информацию по комментарию или списку комментариев.
    """
    user = ProfileSerializer(read_only=True)

    class Meta:
        model = GoalComment
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user', 'goal')


class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Доски создает доски.
    """
    class Meta:
        model = Board
        read_only_fields = ('id', 'created', 'updated', 'is_deleted')
        fields = '__all__'


class BoardParticipantSerializer(serializers.ModelSerializer):
    """
    Сериализатор для реализации связи доска-участники.
    """
    role = serializers.ChoiceField(required=True, choices=BoardParticipant.Role.choices[1:])
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    def validate(self, attrs: dict) -> dict:
        if attrs['user'] == self.context['request'].user and attrs['role'] != BoardParticipant.Role.owner:
            raise ValidationError({'role': 'Failed to update owner role'})
        return attrs

    class Meta:
        model = BoardParticipant
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'board')


class BoardSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Доски выводит информацию по доске.
    """
    participants = BoardParticipantSerializer(many=True)

    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'is_deleted')

    def update(self, instance: Board, validated_data: dict) -> Board:
        with transaction.atomic():
            BoardParticipant.objects.filter(board=instance).exclude(user=self.context['request'].user).delete()
            BoardParticipant.objects.bulk_create([
                BoardParticipant(
                    user=participant['user'],
                    role=participant['role'],
                    board=instance,
                )
                for participant in validated_data.pop('participants', [])
            ])

            if title := validated_data.get('title'):
                instance.title = title
                instance.save(update_fields=('title',))

        return instance


class BoardListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка Досок выводит информацию по доступным доскам.
    """
    class Meta:
        model = Board
        fields = '__all__'
