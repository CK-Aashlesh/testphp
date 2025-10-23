from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
CORS(app)

# -------------------------------
# 🔸 MySQL Database Configuration
# -------------------------------
DB_CONFIG = {
    'host': 'auth-db1829.hstgr.io',
    'database': 'u288092420_nexus',
    'user': 'u288092420_arshad',
    'password': '@Four,ra.2'
}

@app.route('/attendance', methods=['POST'])
def attendance():
    data = request.get_json()

    # Validate incoming data
    required = ["student_id", "first_name", "last_name", "phone_number", "address", "gate_number", "time_in", "date"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = """
            INSERT INTO attendance 
            (student_id, first_name, last_name, phone_number, address, gate_number, time_in, date_in)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """
        values = (
            data["student_id"],
            data["first_name"],
            data["last_name"],
            data["phone_number"],
            data["address"],
            data["gate_number"],
            data["time_in"],
            data["date"]
        )

        cursor.execute(query, values)
        conn.commit()

        return jsonify({"message": "Data inserted successfully"}), 200

    except Error as e:
        print("MySQL Error:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor: cursor.close()
        if conn: conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, ssl_context=('cert.pem', 'key.pem'))  # HTTPS enabled
