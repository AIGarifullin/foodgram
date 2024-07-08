from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthenticatedAuthorOrReadOnly(BasePermission):
    """Права доступа для администратора и автора."""

    message = 'Недостаточно прав для доступа.'

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )
