<?php
// Подключение к Redis
$redis = new Redis();
$redis->connect('127.0.0.1', 6380);

// Функция проверки мобильного устройства
function is_mobile() {
    $user_agent = $_SERVER['HTTP_USER_AGENT'];
    $mobile_devices = ['iphone', 'android', 'blackberry', 'windows phone', 'opera mini', 'mobile', 'ipod'];

    foreach ($mobile_devices as $device) {
        if (stripos($user_agent, $device) !== false) {
            return true;
        }
    }
    return false;
}

// Получаем параметры запроса
$query = $_SERVER['QUERY_STRING'];
parse_str($query, $params);

// Если есть rb_clickid
if (isset($params['rb_clickid'])) {
    $rb_clickid = $params['rb_clickid'];
    $rb_clickid_sha256 = hash('sha256', $rb_clickid);

    // Сохраняем в Redis (8 часов)
    $redis->setex("rb_clickid:$rb_clickid_sha256", 8*60*60, $rb_clickid);

    // Устанавливаем Cookie (Safari-friendly)
    setcookie('rb_clickid', $rb_clickid_sha256, time() + 86400, "/", "", false, true);

    // Убираем rb_clickid из URL перед редиректом
    unset($params['rb_clickid']);
}

// Передаем только SHA256 после start=
$start_param = isset($rb_clickid_sha256) ? $rb_clickid_sha256 : '';

// Определяем URL редиректа
$url = is_mobile()
    ? "tg://resolve?domain=yurchest_chatgpt_bot&start=$start_param"
    : "https://t.me/yurchest_chatgpt_bot?start=$start_param";

// Редиректим
header("Location: $url");
exit();
?>