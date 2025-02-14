<?php
// Конфигурация
const REDIS_HOST = '127.0.0.1';
const REDIS_PORT = 6380;
const REDIS_TIMEOUT = 2; // Таймаут подключения в секундах
const COOKIE_LIFETIME = 8 * 60 * 60; // 8 часов, синхронно с Redis
const MOBILE_PATTERN = '/iPhone|Android|BlackBerry|Windows Phone|Opera Mini|Mobile|iPod/i';

// Обработка ошибок
ini_set('display_errors', 0);
error_reporting(0);

try {
    // Подключение к Redis с обработкой ошибок
    $redis = new Redis();
    if (!$redis->connect(REDIS_HOST, REDIS_PORT, REDIS_TIMEOUT)) {
        throw new RedisException('Failed to connect to Redis');
    }
    
    // Проверка на поддержку Redis
    if (!$redis->ping()) {
        throw new RedisException('Redis server not responding');
    }
} catch (RedisException $e) {
    // Логирование ошибки и редирект на фолбек
    error_log('Redis error: ' . $e->getMessage());
    header('Location: https://t.me/yurchest_chatgpt_bot');
    exit();
}

// Функция проверки мобильного устройства через регулярное выражение
function is_mobile(): bool {
    return !empty($_SERVER['HTTP_USER_AGENT']) 
        && preg_match(MOBILE_PATTERN, $_SERVER['HTTP_USER_AGENT']);
}

// Получаем параметры запроса безопасно
$rb_clickid = filter_input(INPUT_GET, 'rb_clickid', FILTER_SANITIZE_SPECIAL_CHARS);

if ($rb_clickid) {
    // Валидация rb_clickid (пример: длина до 255 символов)
    if (strlen($rb_clickid) > 255) {
        header('HTTP/1.1 400 Bad Request');
        exit('Invalid clickid');
    }
    
    $rb_clickid_sha256 = hash('sha256', $rb_clickid);
    
    try {
        // Сохраняем в Redis с обработкой ошибок
        if (!$redis->setex("rb_clickid:$rb_clickid_sha256", COOKIE_LIFETIME, $rb_clickid)) {
            throw new RedisException('Failed to store clickid');
        }
    } catch (RedisException $e) {
        error_log('Redis write error: ' . $e->getMessage());
    }

    // Устанавливаем безопасные Cookie
    $cookieOptions = [
        'expires' => time() + COOKIE_LIFETIME,
        'path' => '/',
        'domain' => '', // текущий домен
        'secure' => true, // только HTTPS
        'httponly' => true,
        'samesite' => 'Lax' // защита от CSRF
    ];
    
    if (PHP_VERSION_ID < 70300) {
        setcookie('rb_clickid', $rb_clickid_sha256, $cookieOptions['expires'], 
            $cookieOptions['path'], $cookieOptions['domain'], 
            $cookieOptions['secure'], $cookieOptions['httponly']);
    } else {
        setcookie('rb_clickid', $rb_clickid_sha256, $cookieOptions);
    }
}

// Формируем URL для редиректа
$start_param = $rb_clickid_sha256 ?? '';
$encoded_param = urlencode($start_param);
$base_url = is_mobile() 
    ? 'tg://resolve?domain=yurchest_chatgpt_bot' 
    : 'https://t.me/yurchest_chatgpt_bot';

// Собираем конечный URL с экранированием
$redirectUrl = $base_url . ($start_param ? "&start=$encoded_param" : '');

// Проверка заголовков перед отправкой
if (!headers_sent()) {
    header("Location: $redirectUrl", true, 302);
} else {
    // Фолбек для случаев, когда заголовки уже отправлены
    echo "<meta http-equiv='refresh' content='0;URL=$redirectUrl'>";
}
exit();