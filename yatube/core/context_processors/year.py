import datetime


def year(request):
    """Добавляет переменную с актуальным годом"""
    now = datetime.datetime.now()
    return {
        'year': now.year,
    }
