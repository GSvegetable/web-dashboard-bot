import os
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/warehouse')
def warehouse():
    return render_template('warehouse.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
