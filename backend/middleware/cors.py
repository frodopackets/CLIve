"""
CORS middleware configuration for cross-origin requests
"""
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

def add_cors_middleware(app: FastAPI) -> None:
    """
    Add CORS middleware to the FastAPI application
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # React development server
            "http://localhost:5173",  # Vite development server
            "https://*.amazonaws.com",  # CloudFront distributions
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Origin",
            "User-Agent",
            "DNT",
            "Cache-Control",
            "X-Mx-ReqToken",
            "Keep-Alive",
            "X-Requested-With",
            "If-Modified-Since",
        ],
    )