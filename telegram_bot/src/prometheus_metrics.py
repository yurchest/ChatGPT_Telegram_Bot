from prometheus_client import Summary, Histogram, Counter


handler_duration = Histogram('handler_duration_seconds', 'Time spent processing handler' )
count_messages = Counter('messages_count', 'Messages count')