"""
Startup script for the FastAPI application.
Configures the server to work with Render and other deployment environments.
"""
import os
import uvicorn

if __name__ == "__main__":
    # Get port from environment variable (Render provides this)
    # Default to 8000 for local development
    port = int(os.environ.get("PORT", 8000))
    
    # Bind to 0.0.0.0 to accept external connections (required for Render)
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Run the FastAPI application
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
        # Only use reload in development
        reload=os.environ.get("ENV", "production") == "development"
    )
