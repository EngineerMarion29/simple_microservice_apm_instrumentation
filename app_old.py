from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host='mysql',
        user='root',
        password='password',
        database='testdb'
    )

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM professionals')
    professionals = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', professionals=professionals)

if __name__ == '__main__':
    app.run(debug=True)

