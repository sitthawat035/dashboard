# api package — Dashboard backend modules

from flask import request
from flask_limiter import Limiter

# Shared rate limiter instance (initialized in server.py after app creation)
limiter = Limiter(key_func=lambda: request.remote_addr)
