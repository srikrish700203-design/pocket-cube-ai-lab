"""
FastAPI main application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import cube, solve, benchmark, visualize, test_runner, history

app = FastAPI(
    title="Pocket Cube AI Lab API",
    description="2×2 Rubik's Cube state-space search algorithms",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cube.router,       prefix="/api/cube",      tags=["Cube"])
app.include_router(solve.router,      prefix="/api/solve",     tags=["Solve"])
app.include_router(benchmark.router,  prefix="/api/benchmark", tags=["Benchmark"])
app.include_router(visualize.router,  prefix="/api/visualize", tags=["Visualize"])
app.include_router(test_runner.router,prefix="/api/tests",     tags=["Tests"])
app.include_router(history.router,    prefix="/api/history",   tags=["History"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
