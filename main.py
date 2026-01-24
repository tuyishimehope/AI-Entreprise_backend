from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def start():
    return { "message": "Hello world"}