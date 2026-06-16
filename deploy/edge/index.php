<?php

/**
 * Front-controller / roteador do ambiente multi-projeto (BDLP).
 *
 * Roteamento lê $_SERVER['REQUEST_URI'] / QUERY_STRING diretamente — NÃO usa
 * mais o round-trip ?path= do mod_rewrite (que colapsava query repetida,
 * mangleava nomes, perdia encoding e deixava o cliente sobrepor a rota).
 * O .htaccess agora só faz: RewriteRule ^ index.php [L]
 */

function loadEnvFile(string $path): array
{
    if (!file_exists($path)) {
        return [];
    }

    $env = [];
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#')) {
            continue;
        }
        [$key, $value] = array_map('trim', explode('=', $line, 2) + [1 => '']);
        // Remove aspas envolventes ("valor" ou 'valor') — convenção comum de .env.
        if (strlen($value) >= 2) {
            $first = $value[0];
            if (($first === '"' || $first === "'") && substr($value, -1) === $first) {
                $value = substr($value, 1, -1);
            }
        }
        $env[$key] = $value;
    }

    return $env;
}

/**
 * Parser único para PROJECTS e DJANGO_PROJECTS (eram duas cópias quase iguais).
 * $transform: callback opcional aplicado ao valor; se retornar null, o par é
 * descartado (usado para validar a porta do Django).
 */
function parseMapping(string $raw, ?callable $transform = null): array
{
    $mapping = [];
    if ($raw === '') {
        return $mapping;
    }
    foreach (explode(',', $raw) as $pair) {
        if (trim($pair) === '') {
            continue;
        }
        [$code, $value] = array_map('trim', explode(':', $pair, 2) + [1 => '']);
        if ($code === '' || $value === '') {
            continue;
        }
        if ($transform !== null) {
            $value = $transform($value);
            if ($value === null) {
                continue;
            }
        }
        $mapping[strtolower($code)] = $value;
    }

    return $mapping;
}

function getProjectMapping(array $env): array
{
    return parseMapping($env['PROJECTS'] ?? '');
}

function getDjangoMapping(array $env): array
{
    return parseMapping($env['DJANGO_PROJECTS'] ?? '', static function ($port) {
        $portNumber = (int) $port;
        return ($portNumber >= 1 && $portNumber <= 65535) ? $portNumber : null;
    });
}

function applySecurityHeaders(): void
{
    header('X-Content-Type-Options: nosniff');
    header('X-Frame-Options: SAMEORIGIN');
    header('Referrer-Policy: no-referrer');
    header('Permissions-Policy: geolocation=(), microphone=(), camera=()');
}

function send404(): void
{
    applySecurityHeaders();
    http_response_code(404);
    echo '<h1>Projeto não encontrado</h1>';
    echo '<p>O código informado não está cadastrado no ambiente.</p>';
    echo '<p>Verifique suas credenciais de acesso ou consulte o responsável pela configuração.</p>';
    exit;
}

/**
 * Paths que parecem asset estático (têm extensão conhecida). Usado para:
 *  - isentar assets do rate-limit (senão um escritório atrás de NAT estoura
 *    a cota só carregando os ~5 estáticos de cada página);
 *  - no fallback de SPA, devolver 404 honesto em asset ausente em vez de servir
 *    o index.html com 200.
 */
function isStaticAssetPath(string $path): bool
{
    static $assets = [
        'css', 'js', 'mjs', 'map', 'json', 'txt', 'xml',
        'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico', 'avif',
        'woff', 'woff2', 'ttf', 'eot', 'otf',
        'pdf', 'mp4', 'webm', 'wasm', 'zip',
    ];
    $clean = parse_url($path, PHP_URL_PATH);
    $ext = strtolower(pathinfo($clean ?? $path, PATHINFO_EXTENSION));
    return $ext !== '' && in_array($ext, $assets, true);
}

/**
 * Bloqueia, no branch estático, dotfiles em qualquer nível e extensões que
 * nunca devem ser entregues como texto (sobretudo .php — readfile vazaria o
 * código-fonte). Defesa em profundidade além do .htaccess do Apache.
 */
function isForbiddenStaticPath(string $decoded): bool
{
    foreach (explode('/', $decoded) as $segment) {
        if ($segment !== '' && $segment[0] === '.') {
            return true;
        }
    }
    $ext = strtolower(pathinfo($decoded, PATHINFO_EXTENSION));
    static $blocked = [
        'php', 'php3', 'php4', 'php5', 'phtml', 'phar',
        'env', 'sql', 'bak', 'log', 'yaml', 'yml', 'ini', 'dist', 'htaccess',
    ];
    return in_array($ext, $blocked, true);
}

function enforceRateLimit(int $maxRequests = 300, int $windowSeconds = 60): void
{
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $dir = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'bdlp_router';
    if (!is_dir($dir)) {
        @mkdir($dir, 0700, true);
    }
    $file = $dir . DIRECTORY_SEPARATOR . hash('sha256', $ip) . '.json';

    // Anti-symlink: nunca seguir um link plantado por outro usuário no /tmp.
    if (is_link($file)) {
        @unlink($file);
    }

    $now = time();
    $fh = @fopen($file, 'c+');
    if ($fh === false) {
        return; // fail-open: indisponibilidade de IO não pode derrubar o site.
    }
    if (!flock($fh, LOCK_EX)) {
        fclose($fh);
        return;
    }

    // Read-modify-write ATÔMICO sob o mesmo lock (corrige a corrida que
    // subcontava sob concorrência).
    $raw = stream_get_contents($fh);
    $data = ['start' => $now, 'count' => 0];
    $decoded = json_decode((string) $raw, true);
    if (is_array($decoded) && isset($decoded['start'], $decoded['count'])) {
        $data = ['start' => (int) $decoded['start'], 'count' => (int) $decoded['count']];
    }
    if (($now - $data['start']) >= $windowSeconds) {
        $data = ['start' => $now, 'count' => 0];
    }
    $data['count']++;

    rewind($fh);
    ftruncate($fh, 0);
    fwrite($fh, json_encode($data));
    fflush($fh);
    flock($fh, LOCK_UN);
    fclose($fh);

    if ($data['count'] > $maxRequests) {
        applySecurityHeaders();
        header('Retry-After: ' . max(1, $windowSeconds - ($now - $data['start'])));
        http_response_code(429);
        echo 'Too Many Requests';
        exit;
    }
}

function sendFile(string $path): void
{
    if (!is_file($path)) {
        send404();
    }

    applySecurityHeaders();
    $extension = strtolower(pathinfo($path, PATHINFO_EXTENSION));
    $mimeTypes = [
        'html' => 'text/html; charset=UTF-8',
        'htm' => 'text/html; charset=UTF-8',
        'css' => 'text/css; charset=UTF-8',
        'js' => 'application/javascript; charset=UTF-8',
        'mjs' => 'application/javascript; charset=UTF-8',
        'json' => 'application/json; charset=UTF-8',
        'svg' => 'image/svg+xml',
        'png' => 'image/png',
        'jpg' => 'image/jpeg',
        'jpeg' => 'image/jpeg',
        'gif' => 'image/gif',
        'webp' => 'image/webp',
        'ico' => 'image/x-icon',
        'pdf' => 'application/pdf',
        'woff' => 'font/woff',
        'woff2' => 'font/woff2',
        'ttf' => 'font/ttf',
        'eot' => 'application/vnd.ms-fontobject',
        'otf' => 'font/otf',
    ];

    $mimeType = $mimeTypes[$extension] ?? (mime_content_type($path) ?: 'application/octet-stream');
    header('Content-Type: ' . $mimeType);
    header('Content-Length: ' . filesize($path));
    // HTML revalida sempre (SPA shell); demais assets podem ser cacheados um pouco.
    if ($extension === 'html' || $extension === 'htm') {
        header('Cache-Control: no-cache');
    } else {
        header('Cache-Control: public, max-age=300');
    }
    readfile($path);
    exit;
}

/**
 * Proxy reverso transparente via cURL com STREAMING (sem bufferizar a resposta
 * inteira em memória — corrige o estouro de memory_limit em PDFs grandes e a
 * entrega de corpo parcial no timeout). Preserva método, corpo, headers e
 * encoding; reescreve apenas Location/Set-Cookie e remove hop-by-hop.
 *
 * @param string $externalPrefix prefixo público do projeto (ex.: '/Biblioteca')
 *                               ou '' para o fallback de raiz.
 */
function proxyToDjango(int $port, string $subpathRaw, string $rawQuery, string $externalPrefix): void
{
    $path = '/' . ltrim($subpathRaw, '/');
    $target = 'http://127.0.0.1:' . $port . $path;
    if ($rawQuery !== '') {
        $target .= '?' . $rawQuery;
    }

    $method = strtoupper($_SERVER['REQUEST_METHOD'] ?? 'GET');

    // Headers do cliente, menos hop-by-hop e os X-Forwarded-* (que definimos nós
    // — o cliente NÃO pode falsificar IP/host/proto a montante).
    $dropRequest = [
        'host', 'connection', 'proxy-connection', 'keep-alive', 'transfer-encoding',
        'upgrade', 'te', 'content-length', 'forwarded', 'x-real-ip',
        'x-forwarded-for', 'x-forwarded-proto', 'x-forwarded-host', 'x-forwarded-port',
    ];
    $reqHeaders = [];
    if (function_exists('getallheaders')) {
        foreach (getallheaders() as $name => $value) {
            if (in_array(strtolower($name), $dropRequest, true)) {
                continue;
            }
            $reqHeaders[] = $name . ': ' . $value;
        }
    }
    $remote = $_SERVER['REMOTE_ADDR'] ?? '';
    $isHttps = (!empty($_SERVER['HTTPS']) && strtolower((string) $_SERVER['HTTPS']) !== 'off')
        || (($_SERVER['SERVER_PORT'] ?? '') === '443');
    $reqHeaders[] = 'Host: 127.0.0.1:' . $port;
    $reqHeaders[] = 'X-Forwarded-For: ' . $remote;
    $reqHeaders[] = 'X-Real-IP: ' . $remote;
    $reqHeaders[] = 'X-Forwarded-Proto: ' . ($isHttps ? 'https' : 'http');
    if (!empty($_SERVER['HTTP_HOST'])) {
        $reqHeaders[] = 'X-Forwarded-Host: ' . $_SERVER['HTTP_HOST'];
        $reqHeaders[] = 'X-Forwarded-Port: ' . ($_SERVER['SERVER_PORT'] ?? ($isHttps ? '443' : '80'));
    }

    $status = 0;
    $started = false;
    $beginOutput = static function () use (&$started, &$status) {
        if ($started) {
            return;
        }
        if ($status > 0) {
            http_response_code($status);
        }
        $started = true;
    };

    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $target,
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_HTTPHEADER => $reqHeaders,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_RETURNTRANSFER => false,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT => 0,            // sem teto total: downloads grandes podem demorar
        CURLOPT_LOW_SPEED_LIMIT => 1,    // mas aborta um backend pendurado
        CURLOPT_LOW_SPEED_TIME => 60,
        CURLOPT_NOBODY => ($method === 'HEAD'),
        // CURLOPT_ENCODING NÃO setado de propósito: não auto-descomprime, então
        // Content-Encoding/Content-Length do backend seguem coerentes com o corpo.
    ]);
    if ($method !== 'GET' && $method !== 'HEAD') {
        // php://input funciona p/ multipart pois o .htaccess desliga
        // enable_post_data_reading.
        curl_setopt($ch, CURLOPT_POSTFIELDS, file_get_contents('php://input'));
    }

    curl_setopt($ch, CURLOPT_HEADERFUNCTION, function ($ch, $line) use (&$status, $port, $externalPrefix) {
        $len = strlen($line);
        $h = trim($line);
        if ($h === '') {
            return $len;
        }
        if (stripos($h, 'HTTP/') === 0) {
            // Pega o código mesmo SEM reason-phrase ('HTTP/1.1 404' ou 'HTTP/2 404').
            if (preg_match('#^HTTP/\S+\s+(\d{3})#', $h, $m)) {
                $status = (int) $m[1]; // última status-line vence (após 1xx)
            }
            return $len;
        }
        $lower = strtolower($h);
        $dropResponse = [
            'transfer-encoding:', 'connection:', 'keep-alive:', 'server:',
            'x-powered-by:', 'via:', 'upgrade:', 'proxy-connection:', 'date:',
        ];
        foreach ($dropResponse as $d) {
            if (str_starts_with($lower, $d)) {
                return $len;
            }
        }

        if (str_starts_with($lower, 'location:')) {
            $val = trim(substr($h, 9));
            $val = preg_replace('#^https?://127\.0\.0\.1:' . $port . '#i', '', $val);
            // Re-prefixa paths absolutos que não carregam o prefixo do projeto
            // (backends sem script-name, ex.: Node, redirecionam p/ '/login/').
            if ($val !== '' && $val[0] === '/' && $externalPrefix !== '') {
                $needle = $externalPrefix . '/';
                $alreadyPrefixed = strncasecmp($val, $needle, strlen($needle)) === 0
                    || strcasecmp($val, $externalPrefix) === 0;
                if (!$alreadyPrefixed) {
                    $val = $externalPrefix . $val;
                }
            }
            if ($val === '') {
                $val = $externalPrefix !== '' ? $externalPrefix . '/' : '/';
            }
            header('Location: ' . $val, true);
            return $len;
        }

        if (str_starts_with($lower, 'set-cookie:') && $externalPrefix !== '') {
            // Escopa cookies de Path=/ (raiz) para o prefixo do projeto, evitando
            // colisão de sessão/CSRF entre projetos no mesmo host.
            $val = substr($h, 11);
            $val = preg_replace('#;\s*([Pp]ath)=/(?=;|\s|$)#', '; $1=' . $externalPrefix, $val);
            header('Set-Cookie:' . $val, false);
            return $len;
        }

        header($h, false);
        return $len;
    });

    curl_setopt($ch, CURLOPT_WRITEFUNCTION, function ($ch, $data) use ($beginOutput) {
        $beginOutput();
        echo $data;
        return strlen($data);
    });

    // Desliga buffering do PHP para realmente fazer streaming.
    while (ob_get_level() > 0) {
        ob_end_flush();
    }

    $ok = curl_exec($ch);
    $errno = curl_errno($ch);
    curl_close($ch);

    if (!$started) {
        // Resposta sem corpo (204/304/redirect/HEAD) ou erro antes do 1º byte.
        if ($ok === false && $errno !== 0 && $status === 0) {
            http_response_code(502);
            echo 'Bad Gateway';
            exit;
        }
        if ($status > 0) {
            http_response_code($status);
        }
    }
    exit;
}

// ---------------------------------------------------------------------------
// Roteamento
// ---------------------------------------------------------------------------

$env = loadEnvFile(__DIR__ . '/.env');
$projects = getProjectMapping($env);
$djangoProjects = getDjangoMapping($env);
$baseDir = rtrim($env['PROJECT_BASE_DIR'] ?? 'projects', '/') . '/';
$defaultDjango = strtolower(trim($env['DEFAULT_DJANGO_PROJECT'] ?? ''));

// Verdade do roteamento = a URI crua. Sem ?path=, sem $_GET (que colapsa/mangle).
$rawUri = $_SERVER['REQUEST_URI'] ?? '/';
$rawPath = parse_url($rawUri, PHP_URL_PATH);
$rawPath = ($rawPath === null || $rawPath === false) ? '/' : $rawPath;
$rawQuery = $_SERVER['QUERY_STRING'] ?? '';

// Rate-limit conta páginas, não assets (evita 429 de escritório atrás de NAT).
if (!isStaticAssetPath($rawPath)) {
    enforceRateLimit();
}

$trimmed = ltrim($rawPath, '/');
$hasTrailingSlash = ($rawPath !== '/') && str_ends_with($rawPath, '/');

// Encaminha o path completo (cru) ao projeto Django padrão. Usado p/ raiz,
// código inválido (favicon.ico, robots.txt) e código desconhecido.
$proxyDefaultOr404 = static function () use ($defaultDjango, $djangoProjects, $trimmed, $rawQuery) {
    if ($defaultDjango !== '' && isset($djangoProjects[$defaultDjango])) {
        proxyToDjango($djangoProjects[$defaultDjango], $trimmed, $rawQuery, '');
    }
    send404();
};

if ($trimmed === '') {
    $proxyDefaultOr404();
}

$slashPos = strpos($trimmed, '/');
if ($slashPos === false) {
    $codeRaw = $trimmed;
    $subpathRaw = '';
} else {
    $codeRaw = substr($trimmed, 0, $slashPos);
    $subpathRaw = substr($trimmed, $slashPos + 1);
}
$codeDecoded = urldecode($codeRaw);
$code = strtolower($codeDecoded);

// Código inválido → não devolve a página feia do roteador; cai no projeto
// padrão (resolve favicon.ico/robots.txt/sitemap.xml de raiz).
if (!preg_match('/^[a-z0-9_-]{3,64}$/', $code)) {
    $proxyDefaultOr404();
}

$known = isset($djangoProjects[$code]) || isset($projects[$code]);

// Acesso ao código sem barra final → 301 p/ /<code>/ preservando a CAIXA
// original e a query crua (sem vazar o antigo ?path=). Para que assets
// relativos das SPAs e os cookies (case-sensitive) resolvam corretamente.
if ($known && $subpathRaw === '' && !$hasTrailingSlash) {
    applySecurityHeaders();
    $location = '/' . $codeDecoded . '/';
    if ($rawQuery !== '') {
        $location .= '?' . $rawQuery;
    }
    header('Location: ' . $location, true, 301);
    exit;
}

if (isset($djangoProjects[$code])) {
    proxyToDjango($djangoProjects[$code], $subpathRaw, $rawQuery, '/' . $codeDecoded);
}

if (!isset($projects[$code])) {
    $proxyDefaultOr404();
}

$projectPublic = realpath(__DIR__ . '/' . $baseDir . $projects[$code] . '/public');
if ($projectPublic === false || !is_dir($projectPublic)) {
    send404();
}
$projectPublic = rtrim($projectPublic, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR;

$decodedSub = urldecode($subpathRaw);

if ($subpathRaw === '' || $decodedSub === 'index.html' || $decodedSub === 'index.htm') {
    sendFile($projectPublic . 'index.html'); // 404 limpo se não existir
}

if (isForbiddenStaticPath($decodedSub)) {
    send404();
}

$targetPath = realpath($projectPublic . $decodedSub);
if ($targetPath !== false && str_starts_with($targetPath, $projectPublic) && is_file($targetPath)) {
    sendFile($targetPath);
}

// Não encontrado: asset ausente → 404 honesto; rota de SPA (sem extensão) →
// devolve o shell index.html para o roteador client-side.
if (isStaticAssetPath($decodedSub)) {
    send404();
}
sendFile($projectPublic . 'index.html');
