<?php
/**
 * Attendance System MySQL Handler
 * This script receives data from Google Apps Script and stores it in MySQL
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// MySQL Database Configuration
define('DB_HOST', 'sql5.freesqldatabase.com');
define('DB_NAME', 'sql5804209');
define('DB_USER', 'sql5804209');
define('DB_PASS', 'VjasnxFHf9');

// Function to get database connection
function getDBConnection() {
    try {
        $conn = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);
        
        if ($conn->connect_error) {
            throw new Exception("Connection failed: " . $conn->connect_error);
        }
        
        return $conn;
    } catch (Exception $e) {
        http_response_code(500);
        echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
        exit;
    }
}

// Function to create attendance table if not exists
function createTableIfNotExists($conn) {
    $sql = "CREATE TABLE IF NOT EXISTS attendance (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id VARCHAR(50) NOT NULL,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        phone_number VARCHAR(20),
        address TEXT,
        gate_number VARCHAR(20),
        time_in VARCHAR(20),
        time_out VARCHAR(20),
        date VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_student_id (student_id),
        INDEX idx_date (date)
    )";
    
    if (!$conn->query($sql)) {
        throw new Exception("Error creating table: " . $conn->error);
    }
}

// Main execution
try {
    // Only allow POST requests
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        http_response_code(405);
        echo json_encode(['status' => 'error', 'message' => 'Method not allowed']);
        exit;
    }
    
    // Get POST data
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    
    if (!$data) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Invalid JSON data']);
        exit;
    }
    
    // Get database connection
    $conn = getDBConnection();
    
    // Create table if not exists
    createTableIfNotExists($conn);
    
    $action = isset($data['action']) ? $data['action'] : '';
    
    switch ($action) {
        case 'checkin':
            // Insert new check-in record
            $student_id = $conn->real_escape_string($data['student_id']);
            $first_name = isset($data['first_name']) ? $conn->real_escape_string($data['first_name']) : '';
            $last_name = isset($data['last_name']) ? $conn->real_escape_string($data['last_name']) : '';
            $phone_number = isset($data['phone_number']) ? $conn->real_escape_string($data['phone_number']) : '';
            $address = isset($data['address']) ? $conn->real_escape_string($data['address']) : '';
            $gate_number = isset($data['gate_number']) ? $conn->real_escape_string($data['gate_number']) : '';
            $time_in = $conn->real_escape_string($data['time_in']);
            $date = $conn->real_escape_string($data['date']);
            
            $sql = "INSERT INTO attendance 
                    (student_id, first_name, last_name, phone_number, address, gate_number, time_in, date) 
                    VALUES 
                    ('$student_id', '$first_name', '$last_name', '$phone_number', '$address', '$gate_number', '$time_in', '$date')";
            
            if ($conn->query($sql)) {
                $insert_id = $conn->insert_id;
                echo json_encode([
                    'status' => 'success',
                    'message' => 'Check-in recorded',
                    'id' => $insert_id
                ]);
            } else {
                throw new Exception("Error inserting record: " . $conn->error);
            }
            break;
            
        case 'checkout':
            // Update existing record with check-out time
            $student_id = $conn->real_escape_string($data['student_id']);
            $time_out = $conn->real_escape_string($data['time_out']);
            $date = $conn->real_escape_string($data['date']);
            
            // Find the most recent check-in without a check-out for this student on this date
            $sql = "UPDATE attendance 
                    SET time_out = '$time_out' 
                    WHERE student_id = '$student_id' 
                    AND date = '$date' 
                    AND (time_out IS NULL OR time_out = '') 
                    ORDER BY id DESC 
                    LIMIT 1";
            
            if ($conn->query($sql)) {
                if ($conn->affected_rows > 0) {
                    echo json_encode([
                        'status' => 'success',
                        'message' => 'Check-out recorded',
                        'affected_rows' => $conn->affected_rows
                    ]);
                } else {
                    echo json_encode([
                        'status' => 'warning',
                        'message' => 'No matching check-in record found'
                    ]);
                }
            } else {
                throw new Exception("Error updating record: " . $conn->error);
            }
            break;
            
        default:
            http_response_code(400);
            echo json_encode([
                'status' => 'error',
                'message' => 'Invalid action specified'
            ]);
            break;
    }
    
    $conn->close();
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage()
    ]);
}
?>