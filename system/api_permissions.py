from rest_framework.permissions import BasePermission


class HasAnyRolePermission(BasePermission):
    required_roles = ()

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.has_any_role(*self.required_roles)
