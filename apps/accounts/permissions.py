"""Reusable role-based permissions shared across the API."""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import User


class IsAdmin(BasePermission):
    """Allow access only to Admin users (or superusers)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsManager(BasePermission):
    """Allow access only to Manager users."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_manager
        )


class IsAdminOrManager(BasePermission):
    """Allow access to Admin or Manager users."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_admin or user.is_manager)
        )


class IsAdminOrManagerOrReadOnly(BasePermission):
    """Read for any authenticated user; write for Admin/Manager only."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.is_admin or user.is_manager


class RolePermission(BasePermission):
    """
    Generic role gate driven by ``view.allowed_roles``.

    Example:
        class MyView(...):
            permission_classes = [RolePermission]
            allowed_roles = [User.Role.ADMIN, User.Role.MANAGER]
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_admin:
            return True
        allowed_roles = getattr(view, "allowed_roles", None)
        if not allowed_roles:
            return True
        return user.role in {str(role) for role in allowed_roles}


__all__ = [
    "IsAdmin",
    "IsManager",
    "IsAdminOrManager",
    "IsAdminOrManagerOrReadOnly",
    "RolePermission",
    "User",
]
