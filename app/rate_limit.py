"""
Single shared Limiter instance — imported by both main.py (to register it
on the app) and any router that needs @limiter.limit(...) decorators.
Keeping it in its own module avoids a circular import between main.py
and the routers.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
