<?php
header('Content-Type: application/json');
require_once 'config.php';

function sanitizeWildcard($input) {
    // Convert asterisks to SQL wildcards and escape special characters
    $escaped = str_replace(['*', '%', '_'], ['WILDCARD_TEMP', '\%', '\_'], $input);
    $escaped = str_replace('WILDCARD\_TEMP', '%', $escaped);

    return $escaped;
}

function buildQuery($dateQuery, $domainQuery) {
    $conditions = [];
    $params = [];
    
    if (!empty($dateQuery)) {
        $conditions[] = "DATE(firstseen) = ?";
        $params[] = $dateQuery;
    }
    
    if (!empty($domainQuery)) {
        if (strpos($domainQuery, '*') !== false) {
            $conditions[] = "domainname LIKE ?";
            $params[] = sanitizeWildcard($domainQuery);
        } else {
            $conditions[] = "domainname = ?";
            $params[] = $domainQuery;
        }
    }
 
    if (empty($conditions)) {
        throw new Exception("At least one search criteria must be provided");
    }

    $sql = "SELECT * FROM domains WHERE " . implode(' AND ', $conditions) . " ORDER BY domainname LIMIT 1000";

    return [$sql, $params];
}

try {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        throw new Exception("Only POST requests allowed");
    }
    
    $dateQuery = trim($_POST['dateQuery'] ?? '');
    $domainQuery = trim($_POST['domainQuery'] ?? '');
    
    if (empty($dateQuery) && empty($domainQuery)) {
        throw new Exception("Please provide at least one search criteria");
    }
    
    // Validate date format
    if (!empty($dateQuery) && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $dateQuery)) {
        throw new Exception("Invalid date format");
    }
    
    // Basic domain validation (allow wildcards)
    if (!empty($domainQuery) && !preg_match('/^[a-zA-Z0-9\*\.\-_]+$/', $domainQuery)) {
        throw new Exception("Invalid domain format");
    }
    
    $pdo = getConnection();
    list($sql, $params) = buildQuery($dateQuery, $domainQuery);

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $results = $stmt->fetchAll();

    // Convert IP integers to dotted decimal format
    foreach ($results as &$row) {
        if (isset($row['ip']) && $row['ip'] !== null) {
            $row['ip'] = long2ip($row['ip']);
        }
    }
    
    echo json_encode([
        'success' => true,
        'results' => $results,
        'count' => count($results)
    ]);
    
} catch (Exception $e) {
    http_response_code(400);
    echo json_encode([
        'error' => $e->getMessage(),
        'success' => false
    ]);
}
?>
