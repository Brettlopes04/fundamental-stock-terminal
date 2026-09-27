import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from main import app as fastapi_app

class VercelPathMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            orig_uri = None
            for key, val in headers.items():
                k_lower = key.decode("latin1").lower()
                if k_lower in ("x-matched-path", "x-forwarded-uri", "x-vercel-matched-path"):
                    orig_uri = val.decode("latin1").split("?")[0]
                    break
            
            path = scope.get("path", "")
            if orig_uri and orig_uri not in ("/api/index.py", "/api/index"):
                scope["path"] = orig_uri
            elif path in ("/api/index.py", "/api/index", "/api", "/api/"):
                scope["path"] = "/"
                
        await self.app(scope, receive, send)

app = VercelPathMiddleware(fastapi_app)

