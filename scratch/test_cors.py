import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    print("Success")
except Exception as e:
    print(f"Error: {e}")
