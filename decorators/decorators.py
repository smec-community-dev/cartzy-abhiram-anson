from functools import wraps
from django.shortcuts import redirect

def role_required(required_role, login_url):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # 1. Check if logged in
            if not request.user.is_authenticated:
                return redirect(login_url)

            # 2. Check role
            if request.user.role != required_role:
                return redirect(login_url)

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator