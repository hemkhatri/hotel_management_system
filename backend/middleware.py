import os


class FrontendCorsMiddleware:
    """Allow configured browser frontends to call the token API; rejected origins receive no CORS grant."""

    def __init__(self, get_response):
        self.get_response = get_response
        configured = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
        self.allowed_origins = {origin.strip() for origin in configured.split(",") if origin.strip()}

    def __call__(self, request):
        origin = request.headers.get("Origin")
        if request.method == "OPTIONS" and origin in self.allowed_origins:
            # Return the preflight response before authentication so browsers can send Authorization.
            from django.http import HttpResponse
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)
        if origin in self.allowed_origins:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept"
            response["Access-Control-Max-Age"] = "86400"
            response["Vary"] = "Origin"
        return response
