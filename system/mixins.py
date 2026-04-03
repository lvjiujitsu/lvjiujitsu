from django.contrib.auth.mixins import AccessMixin


class RoleRequiredMixin(AccessMixin):
    required_roles = ()

    def has_permission(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        return user.has_any_role(*self.required_roles)

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class OwnerScopeMixin:
    owner_field = "user"

    def scope_queryset(self, queryset):
        user = self.request.user
        if getattr(user, "is_superuser", False):
            return queryset
        return queryset.filter(**{self.owner_field: user})
