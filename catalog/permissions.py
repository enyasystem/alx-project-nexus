from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """Allow read-only access to anyone, but restrict unsafe methods to staff users.

    This is suitable for admin-managed resources like product and category data
    where creation/update/deletion should be done by admins only.
    """

    def has_permission(self, request, view):
        # SAFE_METHODS are GET, HEAD, OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return True
        # For write operations require staff status
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
\n