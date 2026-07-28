#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, jsonify, render_template

app = Flask(__name__, template_folder='templates')
main_sensor_data_ref = None
main_device_id = ""

def init_dashboard_app(sensor_data_ref, device_id=""):
    global main_sensor_data_ref, main_device_id
    main_sensor_data_ref = sensor_data_ref
    main_device_id = device_id

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    if main_sensor_data_ref is not None:
        return jsonify({
            "success": True,
            "device_id": main_device_id,
            "data": main_sensor_data_ref
        })
    return jsonify({"success": False, "device_id": main_device_id, "data": {}})
