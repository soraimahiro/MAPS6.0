# MAPS6.0 WiFi and NB-IoT Version (v7.1.0)

此版本依照 [MAPS6_NTU_Special](https://github.com/SCWhite/MAPS6_NTU_Special) 功能大幅重構，並更新至 v7.1.0。

---

## v7.1.0 重構與修改內容

- 裝置 ID 規範：改回嚴格讀取本機乙太網路網卡 eth0 的硬體 MAC 位址 (/sys/class/net/eth0/address) 作為唯一 DEVIDE_ID。
- 散熱風扇自動控制：補回 set_fan(True) (指令 0xC8，金鑰 "FANc")，開機時自動發送指令至 Mega2560 啟動對流風扇。
- 外殼與板載狀態 LED 控制：補回 set_status_led(1) (指令 0xBC) 與 set_pin_led_all(True) (指令 0xC5，金鑰 "SLED")，開機自動啟用狀態指示燈。
- RTC 硬體時鐘同步：連網後自動呼叫 set_rtc_datetime() (指令 0xC7)，將台北本地時間同步至 Mega2560 RTC 晶片。
- 感測器維護與校正 API：補全 Senseair S8 CO2 400ppm 校正 (set_co2_calibration()) 與 PMS7003 硬體重置/休眠 (set_pms_reset(), set_pms_sleep()) 控制函式。
- Web 監控儀表板 (Port 5000)：內建輕量化網頁儀表板（瀏覽器存取 http://<樹莓派IP>:5000），即時查看溫濕度、PM2.5、CO2、TVOC 數據與 LASS 雲端上傳狀態。靜音 Werkzeug 訪問日誌維持 Docker Logs 乾淨。
- 硬體 Serial 通訊修復：預設選用 /dev/ttyS0 (樹莓派 3 Mini UART)，解決 /dev/ttyAMA0 藍牙介面死鎖問題；當 ENABLE_LTE = False 時自動隔絕 SIM7000E 介面。
- 新增 NBIoT 模組 SIM7000 Library
- 新增 Simcom 專用 MQTT Library（適用 SIM7000、SIM800、SIM7020、AM7020）
- 新增下位機 Mega2560 Library（讀取各感測器資料）
- 移除分貝計相關功能
- 修改主程式流程與本地 CSV 時間：CSV 檔名與內文改採 Asia/Taipei 本地時間戳記。
- 更新 Raspbian 版本 (2021-10-30 armhf-full)
- OLED 加入 NB-IoT 訊號數值（僅在使用 NBIoT 通訊時顯示，訊號範圍 0~31）
- OLED 加入顯示網路連接方式（W: Wifi / N: NBIoT / -: 無網路）
- 自動判斷通訊方式，優先權：WiFi >> NBIoT
- 優化 Docker 與控制腳本：新增 start.sh 控制腳本 (start | stop | reload | restart | logs)，並使用 .dockerignore 防止映像檔巢狀膨脹。

---

## How To Build maps6_v700 Docker Image

### 1. 建立 Docker 映像檔與容器
- 建立 Docker Image (交叉編譯打包 ARMv7)：
  ```bash
  docker buildx build --platform linux/arm/v7 -t maps6_v700:latest --output type=docker,dest=maps6_v700.tar .
  ```
- 建立並執行 Docker Container：
  ```bash
  docker run -itd --restart unless-stopped \
      --net=host \
      --name maps6-nbiot-wifi \
      --privileged \
      maps6_v700:latest
  ```

### 2. 使用一鍵控制腳本 start.sh
```bash
./start.sh reload   # 自動載入 maps6_v700.tar 並重載容器
./start.sh logs     # 查看容器最新 Log
./start.sh stop     # 停止容器
```

---

### 注意事項
- 此版本只適用 MAPS6 Firmware version 1.22 版以上。

---

# For USER

## WiFi 設定方式
1. 按住 MAPS6 AP Mode 按鈕持續 20 秒。
2. 使用行動裝置或筆電連接 WiFi MPAS6_V7.0.0 1.2。
3. 開啟瀏覽器輸入 IP: 10.0.0.1。
4. 選擇目標 WiFi 並輸入密碼。
5. 按下確認鍵後等待 MAPS6 重新啟動即可連接目標 WiFi。

---

## WiFi & NB-IoT 模式
網路使用優先權：WiFi > NB-IoT

- ID：裝置 ID (Ethernet eth0 MAC 位址)
- Date：日期時間
- Temp：溫度
- RH：濕度
- PM2.5：細懸浮微粒
- TVOC：揮發性有機物
- CO2：二氧化碳
- csq：NBIoT 與基地台連接訊號（0~31，建議最低 16，推薦 20 以上）
- Vx.x.x：版本 (v7.1.0)
- 右下角：通訊方式（N: NBIoT, W: WiFi, -: 無任何網路連接）

![NBIOT icon](./images/nb.jpg)
![NBIOT icon](./images/wifi.jpg)

---

## 雲端資料 (LASS Server)
- 進入以下網址查看雲端資料（<device_id> 替換為機器裝置 ID）：
- 資料上傳頻率：每五分鐘一次

https://pm25.lass-net.org/grafana/d/airbox_dashboard2/airdata-coandvoc?orgId=2&var-device_id=<device_id>

![LASS icon](./images/lass_1.png)

---

## 本地資料 (SD 卡)
- 資料存放在 SD 卡/本機目錄中。
- 紀錄頻率：每分鐘一筆 CSV（以 Asia/Taipei 本地時間命名與戳記）。

---

## GPS
- GPS 訊號需要再室外或窗邊才可順利收到衛星定位（無需 SIM 卡即可單獨運作）。

---

## 其他說明資料
- [MAPSV6-使用完全手冊(中英文)](https://maps6-user-guide.gitbook.io/mapsv6-manual-book-zh/)
- [感測器資料格式](https://maps6-user-guide.gitbook.io/mapsv6-manual-book-zh/zi-liao-ge-shi)
- [PM25 Open Data API](https://app.swaggerhub.com/apis-docs/I2875/PM25_Open_Data/1.0.0)
- [MAPS6_NTU_Special/book](https://github.com/SCWhite/MAPS6_NTU_Special/tree/master/book)
- [system.md](file:///Users/mahiro/Documents/project/maps6/new_system/system.md)：Mega2560 封包 Data 位元對照、硬體模組清單與控制規範說明。
- [plan.md](file:///Users/mahiro/Documents/project/maps6/new_system/plan.md)：Go 語言免 Docker 架構重構與模組化需求規劃書。

---

## Lass Server MQTT Protocol Config
- MQTT Broker: 35.162.236.171
- Port: 8883
- MQTT ID: Device ID (eth0 MAC)
- Username: maps
- Password: iisnrl
- Topic: MAPS/MAPS6/<Device ID(MAC)>
