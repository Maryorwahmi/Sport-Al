from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import data_router, prediction_router, training_router
from database.database import engine, Base
import uvicorn

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Sports Analyzer",
    description="Professional AI-powered Sports Analyzer system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data_router.router, prefix="/api/data", tags=["data"])
app.include_router(prediction_router.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(training_router.router, prefix="/api/training", tags=["training"])

@app.get("/")
async def root():
    return {"message": "AI Sports Analyzer API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)