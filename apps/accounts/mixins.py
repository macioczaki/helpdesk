from django.contrib.auth.mixins import LoginRequiredMixin


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles: tuple = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)