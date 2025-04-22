from app.utils_auth import decode_token_from_cookie

def setup_template_globals():
    def inject_globals(request):
        user_id = decode_token_from_cookie(request)
        request.state.is_logged_in = user_id is not None
    return inject_globals
