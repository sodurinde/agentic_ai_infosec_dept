import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("shared.middleware")

class AgentSafetyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Enforce agent authentication and identification check
        agent_id = request.headers.get("X-Agent-ID")
        
        # Public endpoints bypass check (like /health, /ready, /docs)
        if request.url.path in ["/health", "/ready", "/docs", "/openapi.json"]:
            return await call_next(request)
            
        if not agent_id:
            logger.warning(f"Rejected request to {request.url.path} - Missing X-Agent-ID header")
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "message": "Missing mandatory X-Agent-ID header identifying the agent."}
            )

        # Pre-execution Safety Validation (Placeholder for AI Safety Interceptor)
        # Developers of specific agents can extend this to screen prompts for injections
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response
        except Exception as e:
            logger.error(f"Internal server error during processing request: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error", "message": "An error occurred inside the agent microservice."}
            )
