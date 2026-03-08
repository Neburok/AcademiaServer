import uvicorn

from academiaserver.config import SERVER_HOST, SERVER_PORT

if __name__ == "__main__":
    uvicorn.run(
        "academiaserver.api:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=False,
    )
