<?php
$config = [
    'host' => 'localhost',
    'dbname' => 'XXXXXXXXXXXXXXXX',
    'username' => 'XXXXXXXXXXXXXXXX',
    'password' => 'XXXXXXXXXXXXXXXXXX',
    'charset' => 'utf8mb4'
];

function getConnection() {
    global $config;
    try {
        $dsn = "mysql:host={$config['host']};dbname={$config['dbname']};charset={$config['charset']}";
        $pdo = new PDO($dsn, $config['username'], $config['password'], [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false
        ]);
        return $pdo;
    } catch (PDOException $e) {
        throw new Exception("Database connection failed: " . $e->getMessage());
    }
}
?>