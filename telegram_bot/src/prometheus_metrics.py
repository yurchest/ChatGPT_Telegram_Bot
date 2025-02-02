from prometheus_client import Summary, Histogram, Counter

# Метрика для времени ответа (обработки запроса)
MESSAGE_RESPONSE_TIME = Histogram(
    'aiogram_response_duration_seconds',
    'Time spent processing a message',
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]
    )
MESSAGE_RPS_COUNTER = Counter('aiogram_rps', 'Messages count')
ERROR_COUNTER = Counter('aiogram_errors', 'Number of errors in Aiogram', ['error_type'])
