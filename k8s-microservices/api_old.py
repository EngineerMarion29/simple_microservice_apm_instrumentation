from flask import Flask, jsonify, request
import mysql.connector
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.mysql import MySQLInstrumentor

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
MySQLInstrumentor().instrument()

def get_db_connection():
    return mysql.connector.connect(
        host='mysql',
        user='root',
        password='password',
        database='testdb'
    )

@app.route('/api/professionals', methods=['GET'])
def get_professionals():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM professionals')
    professionals = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(professionals)

@app.route('/api/professionals', methods=['POST'])
def add_professional():
    data = request.json
    name = data.get('name')
    profession = data.get('profession')
    years_of_experience = data.get('years_of_experience')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO professionals (name, profession, years_of_experience) VALUES (%s, %s, %s)',
                   (name, profession, years_of_experience))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'success'}), 201

@app.route('/api/professionals/<string:name>', methods=['DELETE'])
def delete_professional(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM professionals WHERE name = %s', (name,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'success'}), 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

