from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

API_BASE_URL = 'http://api-service:5000/api'  # Replace with the actual API service URL

@app.route('/')
def index():
    response = requests.get(f'{API_BASE_URL}/professionals')
    professionals = response.json()
    return render_template('index.html', professionals=professionals)

@app.route('/add', methods=['POST'])
def add_professional():
    data = {
        'name': request.form['name'],
        'profession': request.form['profession'],
        'years_of_experience': request.form['years_of_experience']
    }
    requests.post(f'{API_BASE_URL}/professionals', json=data)
    return redirect(url_for('index'))

@app.route('/delete/<string:name>', methods=['POST'])
def delete_professional(name):
    requests.delete(f'{API_BASE_URL}/professionals/{name}')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

