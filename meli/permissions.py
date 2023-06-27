from rest_framework.permissions import BasePermission

class GroupPermission(BasePermission):
    def has_permission(self, request, view):
        permission_groups = getattr(view, 'permission_groups', None)
        if not permission_groups:
            return True

        user = request.user
        if user.is_superuser:
            return True

        for group_name in permission_groups:
            if user.group != None:
                if user.group.name == group_name:
                    return True