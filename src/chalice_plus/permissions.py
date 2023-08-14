class IsAuthenticated:
    message = "User is not authenticated"

    def has_permission(self, view):
        return view.authenticator.user is not None


class IsAdmin:
    message = "User is not admin"

    def has_permission(self, view):
        user = view.authenticator.user
        return user and user.is_superuser


class IsOwner:
    message = "User is not owner"

    def has_permission(self, view):
        user = view.authenticator.user
        user_id = view.authenticator.user_id
        return user and user_id == view.object.created_by_id


class IsOwnerOrAdmin:
    message = "User is not owner or admin"

    def has_permission(self, view):
        user = view.authenticator.user
        return user and (user.is_superuser or user.id == view.object.created_by_id)
