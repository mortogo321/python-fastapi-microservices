from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def index():
    return {"status": True, "message": "OK"}
