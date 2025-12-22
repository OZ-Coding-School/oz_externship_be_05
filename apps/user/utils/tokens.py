from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.models import User


def issue_token_pair(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {"refresh_token": str(refresh), "access_token": str(refresh.access_token)}
