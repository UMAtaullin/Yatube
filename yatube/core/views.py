from django.shortcuts import render


def page_not_found(request, exception):
    """Переопределение страницы с ошибкой 404."""
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def csrf_failure(request, reason=''):
    """Переопределение страницы с ошибкой 403csrf."""
    return render(request, 'core/403csrf.html')
