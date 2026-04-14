from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import auth, users, products, sales

# Crea las tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CODIT API", version="1.0.0")

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(sales.router)


@app.get("/")
def root():
    return {"message": "CODIT API activa"}
