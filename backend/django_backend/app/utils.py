from django.core.cache import cache
from rest_framework.response import Response
from functools import wraps


def cache_api_view(cache_key, timeout):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            data = cache.get(cache_key)
            if data is not None:
                return Response(data)
            response = view_func(self, request, *args, **kwargs)
            # Cache the response data
            cache.set(cache_key, response.data, timeout)
            return response
        return _wrapped_view
    return decorator
