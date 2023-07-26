import json
from fastapi import FastAPI, Request
from lib.routes import payments, remove_background, add_background
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/feedback")
async def post_feedback(request: Request):
    body = await request.json()
    with open("feedback.json", "a") as file:
        file.write(json.dumps(body))
        file.write("\n")

    return {"message": "Feedback recorded successfully."}


app.include_router(remove_background.router, prefix="/remove_background")
app.include_router(add_background.router, prefix="/add_background")
app.include_router(payments.router, prefix="/payments")
