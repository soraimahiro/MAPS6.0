#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from flask import Flask, jsonify, render_template

# Silence Flask / Werkzeug HTTP access logs
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__, template_folder='templates')
main_sensor_data_ref = None
main_device_id = ""
main_refresh_interval = 5

def init_dashboard_app(sensor_data_ref, device_id="", refresh_interval=5):
    global main_sensor_data_ref, main_device_id, main_refresh_interval
    main_sensor_data_ref = sensor_data_ref
    main_device_id = device_id
    main_refresh_interval = refresh_interval

@app.route('/')
def index():
    return render_template('index.html', refresh_interval=main_refresh_interval)

@app.route('/api/status')
def api_status():
    if main_sensor_data_ref is not None:
        return jsonify({
            "success": True,
            "device_id": main_device_id,
            "data": main_sensor_data_ref
        })
    return jsonify({"success": False, "device_id": main_device_id, "data": {}})
