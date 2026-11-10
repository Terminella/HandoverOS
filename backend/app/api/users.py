from fastapi import APIRouter, HTTPException, Header

from app.api import users_store, sessions


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def get_authenticated_user(
    authorization: str | None
):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    token = authorization.replace(
        "Bearer ", "", 1
    )

    user_id = sessions.get(token)

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    for user in users_store.values():

        if user["id"] == user_id:

            return user

    raise HTTPException(
        status_code=404,
        detail="User not found"
    )


@router.get("/me")
def get_my_profile(
    authorization: str | None = Header(default=None)
):

    user = get_authenticated_user(
        authorization
    )

    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"]
    }


@router.get("/")
def get_all_users(
    authorization: str | None = Header(default=None)
):

    get_authenticated_user(authorization)

    return [

        {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }

        for user in users_store.values()

    ]