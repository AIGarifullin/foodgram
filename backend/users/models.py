from django.contrib.auth.models import AbstractUser
from django.db import models

from users.constants import MAX_LENGTH_EMAIL, MAX_LENGTH_NAME
from users.validators import validate_username


class User(AbstractUser):
    """Модель User (Пользователь)."""

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    email = models.EmailField(verbose_name='Email',
                              max_length=MAX_LENGTH_EMAIL, unique=True,
                              error_messages={
                                  'unique': 'Пользователь с таким'
                                  ' Email уже существует.'})
    username = models.CharField(
        verbose_name='Никнейм пользователя',
        max_length=MAX_LENGTH_NAME,
        unique=True,
        validators=[validate_username],
        error_messages={
            'unique': 'Пользователь с таким именем (никнейном) уже существует.'
        }
    )
    first_name = models.CharField(verbose_name='Имя',
                                  max_length=MAX_LENGTH_NAME,
                                  unique=True)
    last_name = models.CharField(verbose_name='Фамилия',
                                 max_length=MAX_LENGTH_NAME,
                                 unique=True)
    avatar = models.ImageField(verbose_name='Аватар',
                               upload_to='users/images/',
                               null=True,
                               default='default_avatar.png')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель Subscription (Подписка)."""

    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='follower',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='following',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('author',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_author',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_subscribing_to_yourself',
            )
        ]

    def __str__(self):
        return f'{self.user.username} подписан(а) на {self.author.username}.'
