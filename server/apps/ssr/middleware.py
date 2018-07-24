class JSXTemplateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if getattr(request, '_is_jsx_response', False) is True:
            response['content-type'] = 'application/ssr+json'

        return response
