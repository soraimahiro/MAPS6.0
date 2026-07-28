#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mian.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 12/15/2021, 11:43:57 AM

import serial
from time import sleep, perf_counter
import logging
from datetime import datetime
import requests
import os
from enum import Enum
import threading
from os import listdir


from libs.MEGA2560 import mega2560
from libs.MEGA2560.mega2560 import Mega2560
from libs.SIM7000E.sim_access.adapter import MAPS6Adapter
from libs.SIM7000E.sim_access.sim7000E_TCP import SIM7000E_TPC
from libs.SIM7000E.mqtt.mqtt import MQTT
from libs.SSD1306.ssd1306 import SSD1306

logger = logging.getLogger('maps6')
logging.basicConfig(
    # filename='maps6.log',
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s:%(lineno)d - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
logger.setLevel(logging.INFO)


class ConnectionState(Enum):
    NAN = 0
    WIFI = 1
    NBIOT = 2


import dashboard_server

# global variable
ENABLE_LTE = False  # Set to True only if SIM7000E NB-IoT module is attached
UPLOAD_INTERVAL = 300  # second
GET_SENSOR_DATA_INTERVAL = 5  # second
CHECK_WIFI_INTERVAL = 10  # second
SAVE_SD_INTERVAL = 60  # second
REUPLOAD_INTERVAL = 10  # second

# Device config
DEVIDE_ID = open(
    '/sys/class/net/eth0/address').readline().upper().strip().replace(':', '')
MAPS_PI_VERSION = '7.0.0'
APP_ID = 'MAPS6'

# HTTPS config (WiFi)
LASS_REST_URL = 'https://data.lass-net.org/Upload/MAPS-secure.php'

# MQTT config (NBIoT)
BROKER = '35.162.236.171'
MQTT_PORT = 8883
MQTT_ID = DEVIDE_ID
KEEPALIVE = 270
USERNAME = 'maps'
PASSWORD = 'iisnrl'
CLEAR_SESSION = True

TOPIC = f'MAPS/MAPS6/{MQTT_ID}'
QOS = 1

sensor_data = {
    'TEMP': 0.0,
    'HUMI': 0.0,
    'PM2.5_AE': 0,
    'PM1.0_AE': 0,
    'PM10.0_AE': 0,
    'Illuminance': 0,
    'CO2': 0,
    'TVOC': 0
}
connectionState = ConnectionState.NAN
nbiot_csq = '-'
gps_lat = '-'
gps_lon = '-'

nbiot_detected = False


def save_sd_task():
    global sensor_data

    path = "/mnt/SD"
    First_line_data = "Device ID,Date,Time,Temperature,Humidity,PM2.5_AE,PM1.0_AE,PM10.0_AE,Illuminance,CO2,TVOC,longitude,latitude"
    while(True):
        try:
            sleep(SAVE_SD_INTERVAL)
            if sensor_data is None:
                continue
            os.makedirs(path, exist_ok=True)
            time_pairs = datetime.now().strftime("%Y-%m-%d %H:%M:%S").split(' ')
            data_list = [DEVIDE_ID, time_pairs[0], time_pairs[1], sensor_data.get('TEMP', 0), sensor_data.get('HUMI', 0), sensor_data.get('PM2.5_AE', 0),
                         sensor_data.get('PM1.0_AE', 0), sensor_data.get('PM10.0_AE', 0), sensor_data.get(
                             'Illuminance', 0), sensor_data.get('CO2', 0),  sensor_data.get('TVOC', 0),
                         gps_lon, gps_lat]
            data = ','.join([str(d) for d in data_list])
            create_flag = False
            filename = f'{path}/{time_pairs[0]}.csv'
            if(not os.path.isfile(filename)):
                create_flag = True
            with open(filename, 'a+') as f:
                if(create_flag):
                    logger.info(f'Create file: {filename}')
                    f.write(f'{First_line_data}\n')
                f.write(f'{data}\n')
            logger.info('Save sensor data to SD Card.')
        except Exception as e:
            logger.error(e, exc_info=True)


def NBIoT_publish_to_lass(m_mqtt):
    global sensor_data

    pairs = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S").split(' ')
    msg = f"|s_g8={sensor_data.get('CO2', 0)}|s_t0={sensor_data.get('TEMP', 0)}|app={APP_ID}|date={pairs[0]}|s_d0={sensor_data.get('PM2.5_AE', 0)}|s_h0={sensor_data.get('HUMI', 0)}|device_id={DEVIDE_ID}|s_gg={sensor_data.get('TVOC', 0)}|ver_app={MAPS_PI_VERSION}|time={pairs[1]}|MQ"
    gps_data = f"|gps_lon={gps_lon}|gps_lat={gps_lat}"
    if(gps_lon != '-' and gps_lat != '-'):
        msg = gps_data + msg
    logger.info(f'publish message: {msg}')
    return m_mqtt.publish(TOPIC, msg, QOS)


def oled_task():
    global nbiot_csq
    global sensor_data

    oled = SSD1306()
    while True:
        try:
            internet_icon = '-'
            if(connectionState == ConnectionState.WIFI):
                internet_icon = 'W'
                nbiot_csq = '-'
            elif(connectionState == ConnectionState.NBIOT):
                internet_icon = 'N'
            if sensor_data is not None:
                oled.display(DEVIDE_ID, sensor_data.get('TEMP', 0), sensor_data.get('HUMI', 0), sensor_data.get('PM2.5_AE', 0), sensor_data.get('CO2', 0),
                             sensor_data.get('TVOC', 0), internet_icon, MAPS_PI_VERSION, nbiot_csq)
            sleep(0.3)
        except Exception as e:
            logger.error(e, exc_info=True)


def wifi_upload_to_lass():
    global sensor_data

    pairs = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S").split(' ')
    msg = f"|s_g8={sensor_data.get('CO2', 0)}|s_t0={sensor_data.get('TEMP', 0)}|app={APP_ID}|date={pairs[0]}|s_d0={sensor_data.get('PM2.5_AE', 0)}|s_h0={sensor_data.get('HUMI', 0)}|device_id={DEVIDE_ID}|s_gg={sensor_data.get('TVOC', 0)}|ver_app={MAPS_PI_VERSION}|time={pairs[1]}"
    gps_data = f"|gps_lon={gps_lon}|gps_lat={gps_lat}"
    if(gps_lon != '-' and gps_lat != '-'):
        msg = gps_data + msg
    logger.info(f'Upload Message: {msg}')

    get_api = f'{LASS_REST_URL}?topic={APP_ID}&device_id={DEVIDE_ID}&key=NoKey&msg={msg}'
    try:
        res = requests.get(get_api, timeout=10)
        logger.info(f'LASS Upload Response Code: [{res.status_code}], Body: {res.text.strip()}')
        sensor_data['last_upload_code'] = res.status_code
        sensor_data['last_upload_time'] = datetime.now().strftime("%H:%M:%S")
        if res.status_code == 200:
            sensor_data['last_upload_status'] = 'SUCCESS'
            return True
        else:
            sensor_data['last_upload_status'] = f'HTTP {res.status_code}'
    except Exception as e:
        logger.error(f'LASS Upload Exception: {e}')
        sensor_data['last_upload_status'] = 'ERROR'
        sensor_data['last_upload_code'] = 0
        sensor_data['last_upload_time'] = datetime.now().strftime("%H:%M:%S")
    return False


def check_connection(sim7000e_tcp):
    global connectionState
    global nbiot_detected

    if(not os.system('ping www.google.com -q -c 1 -w 2 > /dev/null 2>&1')):
        connectionState = ConnectionState.WIFI
    elif(nbiot_detected and sim7000e_tcp and sim7000e_tcp.network_chkAttach()):
        connectionState = ConnectionState.NBIOT
    else:
        connectionState = ConnectionState.NAN
    logger.info(f'connectionState: {connectionState}')


def check_gps_csq(sim7000e_tcp):
    global nbiot_csq
    global nbiot_detected
    global gps_lat
    global gps_lon

    if(not nbiot_detected or not sim7000e_tcp):
        return
    if(sim7000e_tcp.network_chkAttach()):
        nbiot_csq = sim7000e_tcp.network_getCsq()
    gps_info = sim7000e_tcp.get_gps_info()
    logger.debug(gps_info)
    gps_info_list = gps_info.split(',')
    fix_status = gps_info_list[1]
    if(fix_status == '1'):
        utc_data = gps_info_list[2]
        gps_lat = gps_info_list[3]
        gps_lon = gps_info_list[4]
        logger.info(f'gps get time: {utc_data}')
        logger.info(f'gps lat: {gps_lat} , lon: {gps_lon}')


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    
    port_name = '/dev/ttyS0' if os.path.exists('/dev/ttyS0') else '/dev/ttyAMA0'
    logger.info(f'Opening serial port: {port_name}')
    try:
        m_serial = serial.Serial(port_name, baudrate=115200, timeout=0.1)
    except Exception as e:
        logger.warning(f'Failed to open {port_name}, trying /dev/ttyAMA0: {e}')
        m_serial = serial.Serial('/dev/ttyAMA0', baudrate=115200, timeout=0.1)

    logger.info(f'DEVIDE_ID: {DEVIDE_ID}')
    logger.info(f'MAPS_PI_VERSION: {MAPS_PI_VERSION}')
    logger.info(f'LASS_REST_URL: {LASS_REST_URL}')

    # Init Web Dashboard Server (Port 5000)
    dashboard_server.init_dashboard_app(sensor_data, DEVIDE_ID)
    dashboard_thread = threading.Thread(
        target=lambda: dashboard_server.app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False),
        name="dashboard_web"
    )
    dashboard_thread.daemon = True
    dashboard_thread.start()
    logger.info("Web Dashboard Server started on Port 5000")

    # wait MAPS Boot up
    sleep(2)

    m_sim7000e_tcp = None
    m_mqtt = None
    m_adapter = None

    if ENABLE_LTE:
        try:
            m_adapter = MAPS6Adapter(m_serial)  # UART bridge
            m_sim7000e_tcp = SIM7000E_TPC(m_adapter)  # SIM7000E TCP Command
            m_mqtt = MQTT(m_sim7000e_tcp, BROKER, MQTT_PORT, USERNAME,
                          PASSWORD, KEEPALIVE, MQTT_ID, CLEAR_SESSION)
            nbiot_detected = True
        except Exception as e:
            error = str(e)
            if(error == 'No module or SIM card'):
                logger.info('SIM7000E not detected.')
    else:
        logger.info('LTE/NB-IoT module initialization disabled (ENABLE_LTE=False).')

    m_mega2560 = Mega2560(m_serial)  # Sensor, RTC, polling error count
    logger.info("Initializing Mega2560 MCU over /dev/ttyAMA0...")
    m_mega2560.set_sensor_all_polling()
    logger.info("Mega2560 polling enabled.")

    publish_timer = perf_counter() + UPLOAD_INTERVAL
    get_sensor_timer = 0
    check_wifi_timer = 0

    oled_task_t = threading.Thread(target=oled_task, name="oled_task_t")
    oled_task_t.daemon = True

    save_sd_task_t = threading.Thread(
        target=save_sd_task, name="save_sd_task_t")
    save_sd_task_t.daemon = True

    oled_task_t.start()
    save_sd_task_t.start()
    logger.info("OLED & SD background tasks started.")
    logger.info("Entering main loop...")

    while(True):
        try:
            if(perf_counter() > publish_timer):
                publish_timer = perf_counter() + UPLOAD_INTERVAL
                result = None
                if(connectionState == ConnectionState.WIFI):  # using WiFi
                    result = wifi_upload_to_lass()
                    if(nbiot_detected and m_mqtt):
                        if(m_mqtt.connected()):
                            m_mqtt.disconnect()
                elif(connectionState == ConnectionState.NBIOT):  # using NBIoT
                    if(m_mqtt and not m_mqtt.connected()):
                        logger.info(
                            f'm_mqtt disconnect result: {m_mqtt.disconnect()}')
                        logger.info(
                            f'm_mqtt connect result: {m_mqtt.connect()}')
                    result = NBIoT_publish_to_lass(m_mqtt)
                else:
                    logger.info(
                        'There is no valid network, please check if you can connect to WiFi or NB-IoT')
                if(not result):
                    publish_timer = perf_counter() + REUPLOAD_INTERVAL
                    logger.info('Upload failed, try again in 10 seconds.')
                logger.info(f'upload_to_lass result: {result}')

            # Get All Sensor Data
            if(perf_counter() > get_sensor_timer):
                get_sensor_timer = perf_counter() + GET_SENSOR_DATA_INTERVAL
                new_data = m_mega2560.get_sensor_all()
                if new_data:
                    sensor_data.update(new_data)
                    if(sensor_data.get('CO2') == 65535):
                        sensor_data['CO2'] = -1
                logger.info('='*50)
                for data in sensor_data:
                    logger.info(f'{data}: {sensor_data[data]}')
                logger.info('='*50)

            # Check WiFi valid
            if(perf_counter() > check_wifi_timer):
                check_wifi_timer = perf_counter() + CHECK_WIFI_INTERVAL
                check_connection(m_sim7000e_tcp)
                check_gps_csq(m_sim7000e_tcp)
        except Exception as e:
            logger.error(e, exc_info=True)
        sleep(0.01)
