from fastapi import FastAPI

app = FastAPI(
    title="CS Interview Assistant API"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the CS Interview Assistant API"}