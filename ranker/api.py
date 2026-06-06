from fastapi import FastAPI


app = FastAPI(title="India Runs Ranker API")


@app.get("/")
def root():
    return {"status": "ok", "service": "ranker"}


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}
