import json
from fastapi import Request
from fastapi.routing import APIRouter

router = APIRouter()


@router.post("", include_in_schema=False)
@router.post("/")
async def post_payments(request: Request):
    body = await request.json()
    with open("payments.json", "a") as file:
        file.write(json.dumps(body))
        file.write("\n")

    return {"message": "Payment recorded successfully."}
