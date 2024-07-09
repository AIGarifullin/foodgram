from django.contrib import admin
from django.utils.safestring import mark_safe

from users.models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'email',
                    'username',
                    'first_name',
                    'last_name',
                    'get_avatar',
                    'get_recipes',
                    'get_subscribers')
    search_fields = ('email', 'username')
    list_filter = ('email', 'username')
    list_display_links = ('username',)

    @admin.display(description='Аватар')
    def get_avatar(self, obj):
        if obj.avatar:
            return mark_safe(f'<img src={obj.avatar.url} '
                             'width="40" height="30">')

    @admin.display(description='Количество рецептов')
    def get_recipes(self, obj):
        return obj.recipes.count()

    @admin.display(description='Количество подписчиков')
    def get_subscribers(self, obj):
        return obj.following.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')
