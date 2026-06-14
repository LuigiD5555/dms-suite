from rest_framework import permissions


class IsAuthenticatedAndWriteAllowed(permissions.BasePermission):
    """
    Default permission for the v1 API.

    - Any authenticated user may read.
    - Writes are limited to superusers, staff users, or operational groups.

    This is intentionally conservative because Enterprise DMS stores sensitive
    dossier, identity, document, workflow and employment information.
    Later, this can be replaced by object-level permissions per customer or
    dossier assignment without changing the public URL structure.
    """

    write_groups = {'Admin', 'Superboss', 'Manager'}

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser or request.user.is_staff:
            return True

        return request.user.groups.filter(name__in=self.write_groups).exists()
