from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.initialization import initialize_database
from routes import ai, correspondences, health, lessons, users, words


app = FastAPI(title="Signy PIE API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_event_handler("startup", initialize_database)

for module in (health, users, lessons, words, correspondences, ai):
    app.include_router(module.router)
