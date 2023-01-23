import datetime


def year(request):
    """Добавляет переменную с актуальным годом"""
    return {
        'year': datetime.datetime.now().year,
    }
