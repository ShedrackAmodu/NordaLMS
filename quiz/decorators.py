import functools
import time
from django.contrib import messages

def handle_ai_errors(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except ValueError as e:
            if "API key" in str(e):
                messages.error(request, "AI service is not properly configured. Please contact administrator.")
            else:
                messages.error(request, f"Configuration error: {str(e)}")
            from django.shortcuts import redirect
            return redirect('ai_quiz_config')
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"AI quiz error: {str(e)}")
            messages.error(request, "Failed to generate quiz. Please try again or use fallback questions.")
            from django.shortcuts import redirect
            return redirect('ai_quiz_config')
    return wrapper
