"""
Attendance System MySQL Handler - Python Flask
This script receives data from Google Apps Script and stores it in MySQL
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'sql5.freesqldatabase.com',
    'database': 'sql5804209',
    'user': 'sql5804209',
    'password': 'VjasnxFHf9'
}

def get_db_connection():
    """Create and return database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_table_if_not_exists():
    """Create attendance table if it doesn't exist"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS attendance (
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
        )
        """
        cursor.execute(create_table_query)
        connection.commit()
        return True
    except Error as e:
        print(f"Error creating table: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'Attendance MySQL Handler is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/attendance', methods=['POST'])
def handle_attendance():
    """Main endpoint to handle attendance data"""
    
    # Ensure table exists
    create_table_if_not_exists()
    
    # Get JSON data from request
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400
    
    action = data.get('action', '')
    
    if action == 'checkin':
        return handle_checkin(data)
    elif action == 'checkout':
        return handle_checkout(data)
    else:
        return jsonify({
            'status': 'error',
            'message': 'Invalid action specified'
        }), 400

def handle_checkin(data):
    """Handle check-in operation"""
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'status': 'error',
            'message': 'Database connection failed'
        }), 500
    
    try:
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO attendance 
        (student_id, first_name, last_name, phone_number, address, gate_number, time_in, date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            data.get('student_id', ''),
            data.get('first_name', ''),
            data.get('last_name', ''),
            data.get('phone_number', ''),
            data.get('address', ''),
            data.get('gate_number', ''),
            data.get('time_in', ''),
            data.get('date', '')
        )
        
        cursor.execute(insert_query, values)
        connection.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Check-in recorded successfully',
            'id': cursor.lastrowid,
            'student_id': data.get('student_id')
        }), 200
        
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def handle_checkout(data):
    """Handle check-out operation"""
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'status': 'error',
            'message': 'Database connection failed'
        }), 500
    
    try:
        cursor = connection.cursor()
        
        # Update the most recent check-in without a check-out
        update_query = """
        UPDATE attendance 
        SET time_out = %s 
        WHERE student_id = %s 
        AND date = %s 
        AND (time_out IS NULL OR time_out = '')
        ORDER BY id DESC 
        LIMIT 1
        """
        
        values = (
            data.get('time_out', ''),
            data.get('student_id', ''),
            data.get('date', '')
        )
        
        cursor.execute(update_query, values)
        connection.commit()
        
        if cursor.rowcount > 0:
            return jsonify({
                'status': 'success',
                'message': 'Check-out recorded successfully',
                'affected_rows': cursor.rowcount,
                'student_id': data.get('student_id')
            }), 200
        else:
            return jsonify({
                'status': 'warning',
                'message': 'No matching check-in record found',
                'student_id': data.get('student_id')
            }), 200
        
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/test', methods=['GET'])
def test_connection():
    """Test database connection"""
    connection = get_db_connection()
    if connection:
        if connection.is_connected():
            db_info = connection.get_server_info()
            connection.close()
            return jsonify({
                'status': 'success',
                'message': 'Database connected successfully',
                'mysql_version': db_info
            }), 200
    
    return jsonify({
        'status': 'error',
        'message': 'Database connection failed'
    }), 500

@app.route('/records', methods=['GET'])
def get_records():
    """Get recent attendance records (for testing/monitoring)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({
            'status': 'error',
            'message': 'Database connection failed'
        }), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        student_id = request.args.get('student_id', None)
        
        if student_id:
            query = """
            SELECT * FROM attendance 
            WHERE student_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """
            cursor.execute(query, (student_id, limit))
        else:
            query = """
            SELECT * FROM attendance 
            ORDER BY created_at DESC 
            LIMIT %s
            """
            cursor.execute(query, (limit,))
        
        records = cursor.fetchall()
        
        return jsonify({
            'status': 'success',
            'count': len(records),
            'records': records
        }), 200
        
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    # Create table on startup
    create_table_if_not_exists()
    
    # Run the Flask app
    # For production, use a proper WSGI server like Gunicorn
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)