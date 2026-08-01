import os, requests, asyncio, threading
from flask import Flask, render_template

app = Flask(__name__)

# 主路由：显示你的后台界面
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
