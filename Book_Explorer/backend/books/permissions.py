from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Object-level permission to only allow owners of an 
    object to edit it. Read-only requests are allowed for everyone.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request (GET, HEAD, OPTIONS).
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed for the owner of the object.
        return obj.user == request.user