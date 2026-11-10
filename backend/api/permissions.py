from rest_framework.permissions import SAFE_METHODS, BasePermission

from .authentication import RobotPrincipal


class IsHumanAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and not isinstance(request.user, RobotPrincipal))


class IsOperatorOrAdmin(IsHumanAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.user.is_superuser or request.user.groups.filter(name__in=["Administrateur", "Operateur"]).exists()
        )


class IsOperatorOrAdminOrReadOnly(IsHumanAuthenticated):
    """Permet la consultation (GET, HEAD, OPTIONS) à tout humain authentifié.
    La création, modification et suppression sont réservées aux Opérateurs et Administrateurs."""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user.is_superuser or request.user.groups.filter(name__in=["Administrateur", "Operateur"]).exists()
        )


class IsAdminRole(IsHumanAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.user.is_superuser or request.user.groups.filter(name="Administrateur").exists()
        )


class IsRobotAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, RobotPrincipal)
