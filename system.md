# MAPS 6.0 系統硬體模組與 Data 位元對照規範文件

本文件詳細紀錄 MAPS 6.0 樹莓派環境監測盒子中所有硬體模組、Mega2560 MCU 封包 Data 位元對照、數值意義、控制方式、金鑰防護機制、雙重 SD 儲存架構、GPS與LTE運作機制、OLED 顯示規範與完整常數列表。

## MCU 串口通訊指令與金鑰總常數表

Mega2560 MCU 透過 UART 串口（/dev/ttyS0 @ 115200 8N1）與樹莓派通訊。通訊封包格式固定為 Start(0xAA, 0x55) + Cmd + ~Cmd + Payload + Checksum(CS, ~CS)。

下表列出系統所有 MCU 串口指令碼、驗證金鑰與回應長度：

| 指令碼 (CMD Hex) | 指令名稱 | 隨附驗證金鑰 (ASCII / Hex Key) | 請求 Payload 長度 | 回應封包總長度 | 指令功能與說明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0xB0 | GET_TEMP_HUM | 無 | 0 Bytes | 8 Bytes | 單獨讀取 SHT3x 溫濕度數據 |
| 0xB1 | GET_CO2 | 無 | 0 Bytes | 8 Bytes | 單獨讀取 Senseair S8 CO2 數據 |
| 0xB2 | GET_TVOC | 無 | 0 Bytes | 16 Bytes | 單獨讀取 Sensirion SGP30 TVOC/eCO2 數據 |
| 0xB3 | GET_LIGHT | 無 | 0 Bytes | 16 Bytes | 單獨讀取 TCS34725 / AS7262 光學照度數據 |
| 0xB4 | GET_PMS | 無 | 0 Bytes | 16 Bytes | 單獨讀取 PMS7003 懸浮微粒數據 |
| 0xB5 | GET_SENSOR_ALL | 無 | 0 Bytes | 48 Bytes | 批次讀取全套 22 欄位感測器數據 |
| 0xB6 | GET_INFO_VERSION | 無 | 0 Bytes | 6 Bytes | 讀取 MCU 韌體版本號 |
| 0xB7 | GET_INFO_RUNTIME | 無 | 0 Bytes | 9 Bytes | 讀取 MCU 系統連續運算天、時、分、秒 |
| 0xB8 | GET_INFO_ERROR_LOG | 無 | 0 Bytes | 16 Bytes | 讀取硬體感測器通訊 Timeout/Error 統計次數 |
| 0xB9 | GET_INFO_SENSOR_POR | 無 | 0 Bytes | 16 Bytes | 讀取感測器上電重置歷史與 Polling 啟用狀態 |
| 0xBA | GET_RTC_DATE_TIME | 無 | 0 Bytes | 10 Bytes | 讀取 MCU 板載 RTC 晶片即時日期時間 |
| 0xBB | GET_INFO_PIN_STATE | 無 | 0 Bytes | 11 Bytes | 唯讀查詢 MCU GPIO 各硬體腳位開關狀態 |
| 0xBC | SET_STATUS_LED | 無 | 2 Bytes (State ms) | 4 Bytes | 設定外殼 ST 狀態燈閃爍週期毫秒數 |
| 0xC0 | SET_PIN_CO2_CAL | S8LP / [0x53, 0x38, 0x4C, 0x50] | 5 Bytes (Key + 0x01) | 4 Bytes | 觸發 Senseair S8 CO2 大氣 400ppm 基準校正 |
| 0xC1 | SET_PIN_PMS_RESET | PMS3 / [0x50, 0x4D, 0x53, 0x33] | 5 Bytes (Key + 0x01) | 4 Bytes | 觸發 PMS7003 懸浮微粒感測器硬體重置 |
| 0xC2 | SET_PIN_PMS_SET | 3003 / [0x33, 0x30, 0x30, 0x33] | 5 Bytes (Key + 0x01/0x00) | 4 Bytes | 控制 PMS7003 雷射感測器進入省電休眠或喚醒 |
| 0xC3 | SET_PIN_NBIOT_PWRKEY | NB-I / [0x4E, 0x42, 0x2D, 0x49] | 5 Bytes (Key + 0x01) | 4 Bytes | 觸發 SIM7000E PWRKEY 脈衝腳位 1.2 秒開關機 |
| 0xC4 | SET_PIN_NBIOT_SLEEP | -IOT / [0x2D, 0x49, 0x4F, 0x54] | 5 Bytes (Key + 0x01/0x00) | 4 Bytes | 控制 DTR 腳位使 SIM7000E 進入極低功耗休眠 |
| 0xC5 | SET_PIN_LED_ALL | SLED / [0x53, 0x4C, 0x45, 0x44] | 5 Bytes (Key + 0x01/0x00) | 4 Bytes | 全板 6-LED 總電源開關 (Master LED Switch) |
| 0xC6 | SET_POLLING_SENSOR | 無 | 6 Bytes (Switches) | 4 Bytes | 設定 6 大感測器 MCU 背景硬體輪詢開關 |
| 0xC7 | SET_RTC_DATE_TIME | 無 | 6 Bytes (YY MM DD hh mm ss) | 4 Bytes | 寫入並同步樹莓派系統時間至 MCU RTC 晶片 |
| 0xC8 | SET_PIN_FAN_ALL | FANc / [0x46, 0x41, 0x4E, 0x63] | 5 Bytes (Key + 0x01/0x00) | 4 Bytes | 切換盒子散熱風扇強制對流開關 |
| 0xCA | PROTOCOL_I2C_WRITE | 無 | N Bytes (Addr, Reg, Data) | 4 Bytes | MCU 代為透傳 I2C 寫入操作 |
| 0xCB | PROTOCOL_I2C_READ | 無 | N Bytes (Addr, Reg, Len) | 6+N Bytes | MCU 代為透傳 I2C 讀取操作 |
| 0xCC | PROTOCOL_UART_BEGIN | 無 | 3 Bytes (Port, Baud, Format) | 4 Bytes | 初始化 MCU UART 通道與波特率轉發模式 |
| 0xCD | PROTOCOL_UART_TX_RX | 無 | 9+N Bytes (Port, TxLen, RxLen, Timeout) | 6+N Bytes | 發送 AT 指令並由 MCU 代為等待接收回應 |
| 0xCE | PROTOCOL_UART_TXRX_EX | 無 | 8+N Bytes (Port, TxLen, ByteTO, WaitTO, Data) | 6+N Bytes | 擴展版 UART 收發指令，支援自訂 ByteTimeout 與 WaitTimeout |
| 0xCF | ENABLE_UART_ACTIVE_RX | 無 | 6 Bytes (Port, En, Poll, ByteTO, RcvTO) | 4 Bytes | 啟用 MCU 對外接 UART 模組主動接收轉發 |

## GET_SENSOR_ALL (0xB5) 感測器數據 42 Bytes Payload 位元對照表

當發送 0xB5 指令時，MCU 回傳 48 Bytes 封包。其中 index 2 至 45 共 44 位元組為 Payload Data (包含 Leading AA B5)。

數據結構欄位對照如下：

| 數據 Payload 位元 (Bytes) | 封包位元 (data[N]) | 模組 / 感測器名稱 | 欄位代號 | 數值計算與數據意義 | 單位 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Bytes [0:2] | data[2:4] | SHT3x 溫濕度感測器 | TEMP | int16 / 100.0 (環境溫度) | ℃ |
| Bytes [2:4] | data[4:6] | SHT3x 溫濕度感測器 | HUMI | int16 / 100.0 (相對濕度) | %RH |
| Bytes [4:6] | data[6:8] | Senseair S8 CO2 感測器 | CO2 | uint16 (65535 代表無回應/初始化中，建議轉換為 -1) | ppm |
| Bytes [6:8] | data[8:10] | Senseair S8 CO2 感測器 | AVE_CO2 | uint16 (平均 CO2 濃度) | ppm |
| Bytes [8:10] | data[10:12] | Sensirion SGP30 有機物 | TVOC | uint16 (總揮發性有機化合物) | ppb |
| Bytes [10:12] | data[12:14] | Sensirion SGP30 有機物 | eCO2 | uint16 (等效 CO2 估算值) | ppm |
| Bytes [12:14] | data[14:16] | Sensirion SGP30 有機物 | S_H2 | uint16 (獨立原始氫氣 Raw 訊號，可用於單獨觀察氣體基線) | Raw |
| Bytes [14:16] | data[16:18] | Sensirion SGP30 有機物 | S_ETHANOL | uint16 (獨立原始乙醇/酒精 Raw 訊號，可用於單獨觀察酒精蒸氣) | Raw |
| Bytes [16:18] | data[18:20] | Sensirion SGP30 有機物 | BASELINE_TVOC | uint16 (TVOC 校正基準值) | Raw |
| Bytes [18:20] | data[20:22] | Sensirion SGP30 有機物 | BASELINE_eCO2 | uint16 (eCO2 校正基準值) | Raw |
| Bytes [20:22] | data[22:24] | TCS34725 / AS7262 照度 | Illuminance | uint16 (環境光照強度) | Lux |
| Bytes [22:24] | data[24:26] | TCS34725 / AS7262 色溫 | Color_Temperature | uint16 (環境色溫) | °K |
| Bytes [24:26] | data[26:28] | 光學色彩感測器 | CH_R | uint16 (紅色光 Raw 通道) | Raw |
| Bytes [26:28] | data[28:30] | 光學色彩感測器 | CH_G | uint16 (綠色光 Raw 通道) | Raw |
| Bytes [28:30] | data[30:32] | 光學色彩感測器 | CH_B | uint16 (藍色光 Raw 通道) | Raw |
| Bytes [30:32] | data[32:34] | 光學色彩感測器 | CH_C | uint16 (全光譜 Clear Raw 通道) | Raw |
| Bytes [32:34] | data[34:36] | PMS7003 懸浮微粒感測器 | PM1.0_AE | uint16 (大氣環境 PM1.0 濃度) | μg/m³ |
| Bytes [34:36] | data[36:38] | PMS7003 懸浮微粒感測器 | PM2.5_AE | uint16 (大氣環境 PM2.5 濃度) | μg/m³ |
| Bytes [36:38] | data[38:40] | PMS7003 懸浮微粒感測器 | PM10.0_AE | uint16 (大氣環境 PM10 濃度) | μg/m³ |
| Bytes [38:40] | data[40:42] | PMS7003 懸浮微粒感測器 | PM1.0_SP | uint16 (標準顆粒 PM1.0 濃度) | μg/m³ |
| Bytes [40:42] | data[42:44] | PMS7003 懸浮微粒感測器 | PM2.5_SP | uint16 (標準顆粒 PM2.5 濃度) | μg/m³ |
| Bytes [42:44] | data[44:46] | PMS7003 懸浮微粒感測器 | PM10.0_SP | uint16 (標準顆粒 PM10 濃度) | μg/m³ |

## MCU 診斷與資訊查詢回應明細表

系統提供多個診斷指令供健康檢查與除錯，其回應封包欄位明細如下：

### 硬體腳位狀態查詢 0xBB (GET_INFO_PIN_STATE)

發送 AA 55 BB 44，MCU 回應 11 Bytes（data[0:2] 為 AA BB）：

| Payload 位元 | 欄位變數名稱 | 數據意義與型態 | 代表硬體狀態 |
| :--- | :--- | :--- | :--- |
| data[2] | PIN_CO2_CAL | uint8 (0 / 1) | Senseair S8 CO2 校正腳位狀態 |
| data[3] | PIN_PMS_RESET | uint8 (0 / 1) | PMS7003 重置腳位狀態 |
| data[4] | PIN_PMS_SET | uint8 (0 / 1) | PMS7003 休眠腳位狀態 |
| data[5] | PIN_NBIOT_PWRKEY | uint8 (0 / 1) | SIM7000E PWRKEY 按鈕脈衝腳位狀態 |
| data[6] | PIN_NBIOT_SLEEP | uint8 (0 / 1) | SIM7000E DTR 休眠腳位狀態 |
| data[7] | PIN_LED_CTRL | uint8 (0 / 1) | 板載 6-LED 總電源開關狀態 |
| data[8] | PIN_FAN_CTRL | uint8 (0 / 1) | 散熱風扇電源開關狀態 |
| data[9:11] | Checksum | uint8, uint8 | CS, ~CS 校驗碼 |

### 系統運轉時間查詢 0xB7 (GET_INFO_RUNTIME)

發送 AA 55 B7 48，MCU 回應 9 Bytes（data[0:2] 為 AA B7）：

| Payload 位元 | 欄位變數名稱 | 數據計算與型態 | 數據意義 |
| :--- | :--- | :--- | :--- |
| data[2:4] | RT_DAY | uint16 (data[3]*256 + data[2]) | 連續運算累積天數 (Days) |
| data[4] | RT_HOUR | uint8 | 累積小時數 (0-23 Hours) |
| data[5] | RT_MIN | uint8 | 累積分鐘數 (0-59 Minutes) |
| data[6] | RT_SEC | uint8 | 累積秒數 (0-59 Seconds) |
| data[7:9] | Checksum | uint8, uint8 | CS, ~CS 校驗碼 |

### 硬體錯誤日誌統計查詢 0xB8 (GET_INFO_ERROR_LOG)

發送 AA 55 B8 47，MCU 回應 16 Bytes（data[0:2] 為 AA B8）：

| Payload 位元 | 欄位變數名稱 | 數據計算與型態 | 代表感測器通訊錯誤統計 |
| :--- | :--- | :--- | :--- |
| data[2:4] | ERROR_TEMP_HUM | uint16 (data[3]*256 + data[2]) | SHT3x 溫濕度通訊失敗累計次數 |
| data[4:6] | ERROR_CO2 | uint16 (data[5]*256 + data[4]) | Senseair S8 CO2 通訊失敗累計次數 |
| data[6:8] | ERROR_TVOC | uint16 (data[7]*256 + data[6]) | Sensirion SGP30 有機物通訊失敗累計次數 |
| data[8:10] | ERROR_LIGHT | uint16 (data[9]*256 + data[8]) | TCS34725 照度色溫通訊失敗累計次數 |
| data[10:12] | ERROR_PMS | uint16 (data[11]*256 + data[10]) | PMS7003 懸浮微粒通訊失敗累計次數 |
| data[12:14] | ERROR_RTC | uint16 (data[13]*256 + data[12]) | RTC 時鐘晶片通訊失敗累計次數 |
| data[14:16] | Checksum | uint8, uint8 | CS, ~CS 校驗碼 |

## 外殼與板載狀態指示燈號規畫

擴充板實體配置 6 個狀態指示燈：
* 1V8：1.8V 電源指示燈（紅燈，正常運作時持續長亮）。
* 3V3：3.3V 電源指示燈（綠燈，正常運作時持續長亮）。
* 5V：5.0V 電源指示燈（綠燈，正常運作時持續長亮）。
* ST：系統狀態燈（Status LED，依據指令 0xBC 設定的週期時間閃爍）。
* TX / RX：UART 串口傳輸與接收指示燈（資料封包通過時閃爍，平時不亮）。

控制指令與交互行為規範：
* 0xBC (SET_STATUS_LED)：僅設定 ST 燈的閃爍週期 (ms)。State = 0 為關閉，State = 1 為 1ms 最快閃爍，State = 2 ~ 65534 為閃爍週期 (ms)。
* 0xC5 (SET_PIN_LED_ALL)：全板 LED 總電源開關 (Master LED Switch)（金鑰 SLED）。State = 1 開啟全板 LED 電源，1V8/3V3/5V 恢復常亮，ST 燈繼續維持 0xBC 設定的頻率運作。State = 0 強制關閉所有 6 個 LED（夜間暗房/省電模式）。

## SIM7000E LTE 與 GPS 系統架構與控制規範 (完全基於原始碼分析)

本章節完全依據專案原始碼（system_v7/main.py, libs/SIM7000E/sim_access/adapter.py, simcom.py, sim7000E_TCP.py 與 ATCommands.py）進行系統運作機制之梳理。

### 1. 通訊介面與 MCU 串口透傳架構 (MAPS6Adapter)

在 system_v7/main.py 第 222 行與 253 行中，樹莓派與 SIM7000E 的物理通訊完全透過 40-Pin GPIO 串口 (/dev/ttyS0 @ 115200 波特率) 連接至 Mega2560 MCU，再由 MCU 透傳至 SIM7000E 模組。

通訊由 libs/SIM7000E/sim_access/adapter.py 中之 MAPS6Adapter 類別進行三階段封裝：
* 階段 1：初始化 UART0 通道 ➔ 寫入 0xCC (MAPS_UART_BEGIN_CMD，Payload 0x00 0x04 0x00)，等待 MCU 回應 ACK (0xAA 0xCC 0x00 0xFF)。
* 階段 2：啟用主動 RX 轉發 ➔ 寫入 0xCF (MAPS_UART_ENABLE_ACTIVE_RX_CMD)，帶入 Port=0x00, Enable=True, Polling=100, ByteTimeout=50, RcvTimeout=10000，等待 MCU 回應 ACK (0xAA 0xCF 0x00 0xFF)。
* 階段 3：發送 AT 指令與接收響應 ➔ 寫入 0xCD (MAPS_UART_TX_RX_CMD)，將 AT 命令文字封裝於 Header 中發送；當 SIM7000E 回應時，MCU 會發送 0xD0 (MAPS_ECHO_UART_ACTIVE_RX_CMD) 封包將模組文字轉發回樹莓派。

### 2. 模組檢查與初始化流程 (SIMModuleBase)

在 libs/SIM7000E/sim_access/simcom.py 中，SIM7000E 啟動時執行以下 AT 控制流程：
* 通訊測試：發送 AT\r\n (ATCommands.test())，等待回應 OK\r\n。
* SIM 卡狀態檢查：發送 AT+CPIN?\r\n (ATCommands.module_checkready())。若未插 SIM 卡，模組回應 +CME ERROR，系統拋出 module not ready；若 SIM 卡正常，回應 +CPIN: READY。
* 關閉迴響：發送 ATE0\r\n (ATCommands.module_setecho(False))，關閉指令迴響。

### 3. GPS 衛星定位系統動態實作 (get_gps_info)

在 libs/SIM7000E/sim_access/simcom.py 第 181-198 行中，GPS 定位由 get_gps_info() 方法獨立執行：
* 步驟 1 (開啟天線電源)：發送 AT+CGNSPWR=1\r\n (ATCommands.Gnss_Pwr_on())，開啟 GNSS 衛星天線電源。
* 步驟 2 (查詢導航數據)：發送 AT+CGNSINF\r\n (ATCommands.Gnss_Navigation_info())，讀取包含 +CGNSINF: 的回應字串。
* 數據解析邏輯 (main.py check_gps_csq)：
  將 +CGNSINF: 後續字串依逗號切割 (split(','))：
  * parts[1] (Fix Status)：等於 '1' 代表衛星定位成功鎖定；等於 '0' 代表正在搜尋衛星。
  * parts[2]：UTC 定位日期與時間。
  * parts[3]：緯度 (gps_lat)。
  * parts[4]：經度 (gps_lon)。

### 4. LTE NB-IoT 網路與 MQTT 上傳實作 (SIM7000E_TPC & MQTT)

在 libs/SIM7000E/sim_access/sim7000E_TCP.py 與 libs/SIM7000E/mqtt/mqtt.py 中：
* 訊號強度查詢 (network_getCsq)：發送 AT+CSQ\r\n，解析 +CSQ: <rssi>,<ber> 取得訊號強度 nbiot_csq。
* 網路附著檢查 (network_chkAttach)：發送 AT+CGATT?\r\n，確認回應是否為 +CGATT: 1。
* 自動獲取 APN (network_getapn)：發送 AT+CGNAPN\r\n 取得電信商 APN 並呼叫 AT+CSTT 設定。
* TCP / MQTT 連線：呼叫 AT+CIPRXGET=1 設為手動收包、AT+CIPSENDHEX=1 設為 Hex 模式，發送 AT+CIPSTART="TCP","35.162.236.171",8883 建立通道。透過 m_mqtt.publish() 將 LASS 格式字串傳送至 MQTT Broker。

MQTT 連線參數常數表：

| 參數名稱 | 常數值 | 說明 |
| :--- | :--- | :--- |
| BROKER | 35.162.236.171 | MQTT Broker 伺服器 IP |
| MQTT_PORT | 8883 | MQTT 連線 Port (TLS) |
| USERNAME | maps | MQTT 認證帳號 |
| PASSWORD | iisnrl | MQTT 認證密碼 |
| KEEPALIVE | 270 秒 | MQTT 心跳保持間隔 |
| TOPIC | MAPS/MAPS6/{DEVICE_ID} | MQTT 發佈主題格式 |
| QOS | 1 | 發佈訊息服務品質等級 |
| CLEAR_SESSION | True | 每次連線清除舊 Session |

### 5. MCU 側硬體腳位控制

在 libs/MEGA2560/mega2560.py 中：
* 0xC3 (SET_PIN_NBIOT_PWRKEY)：隨附金鑰 NB-I ([0x4E, 0x42, 0x2D, 0x49])。MCU 產生 1.2 秒 PWRKEY 腳位拉低脈衝，觸發模組軟體開關機。
* 0xC4 (SET_PIN_NBIOT_SLEEP)：隨附金鑰 -IOT ([0x2D, 0x49, 0x4F, 0x54])。控制 DTR 腳位切換休眠模式。

### 6. 主程式系統開關邏輯 (main.py)

* 在 system_v7/main.py 第 44 行中，全域變數預設 ENABLE_LTE = False。
* 系統預設優先使用本機 WiFi 連線 (ConnectionState.WIFI)；當 WiFi 無法連通且 nbiot_detected 為 True 時，系統會自動切換至 NB-IoT 模式 (ConnectionState.NBIOT) 上傳數據。

## OLED 顯示模組 (SSD1306 128x64) 資訊與顯示規範

OLED 顯示模組採用 SSD1306 驅動晶片，解析度為 128×64 像素。OLED 模組透過獨立的硬體 I2C 匯流排連接於樹莓派，不經過 MCU 串口。

### SSD1306 模組常數與硬體介面表

| 項目名稱 | 硬體參數與常數值 | 說明 |
| :--- | :--- | :--- |
| 匯流排路徑 | /dev/i2c-1 | 樹莓派主板硬體 I2C1 裝置 |
| I2C 標準位址 | 0x3C | SSD1306 OLED 晶片標準 7-bit Slave Address |
| 螢幕解析度 | 128 × 64 像素 (Pixels) | 寬 128 點，高 64 點單色點陣 |
| 渲染字型 | ARIALUNI.TTF | 預設載入字型，使用 9pt 與 14pt 兩種字體大小 |
| 重整頻率 | 300 ms (約 3.3 Hz) | 預設畫面刷新間隔時間 |

### OLED 預設頁面 (Status Screen) Layout 規範

在狀態模式下，OLED 螢幕繪製 6 行主體文字（累加式 Y 位移，cur_y += font_size）加上 3 個絕對座標元素：

| 螢幕行別 (Line) | 繪製 Y 座標 | 字體大小 | 顯示內容與範例 |
| :--- | :--- | :--- | :--- |
| Line 1 | Y = 0 | 14 pt (大字) | ID: B827EB52FDBC (顯示樹莓派 MAC 轉成之 Device ID) |
| Line 2 | Y = 14 | 9 pt | Date: 2026-08-13 17:00:00 (系統日期與時間，合併一行) |
| Line 3 | Y = 23 | 9 pt | Temp: 25.5 / RH: 60.0 (溫濕度數據) |
| Line 4 | Y = 32 | 9 pt | PM2.5: 15 μg/m3 (PM2.5 濃度) |
| Line 5 | Y = 41 | 9 pt | TVOC: 120 ppb (TVOC 濃度) |
| Line 6 | Y = 50 | 9 pt | CO2: 450 ppm (CO2 濃度) |
| (絕對座標) | (80, 40) | 9 pt | csq: {CSQ 信號強度} (右側疊加顯示) |
| (絕對座標) | (80, 51) | 9 pt | V8.0.0 版本號 |
| (絕對座標) | (117, 51) | 9 pt | W (WiFi) 或 N (NB-IoT) 連線狀態旗標 |

## 雙重 SD 卡儲存架構分析 (Dual SD Architecture)

系統設計包含兩層獨立的 SD 卡儲存層級：
* 樹莓派系統主卡 (/dev/mmcblk0)：安裝 Linux OS，並透過 Docker 容器掛載 /mnt/SD 目錄寫入本機備份數據（宿主機實際路徑為啟動腳本同目錄下的 ./data 資料夾）。
* 訂製擴充板 SPI SD 卡槽 (/dev/mmcblk2p1 / /mnt/SD)：經由 SPI0 匯流排獨立連接於擴充板上，支援離線脫機備份。即使樹莓派系統損壞，拔下擴充板上的 SD 卡即可直接救回歷史 CSV 數據。

## WiFi HTTPS 數據上傳機制

系統預設以 WiFi 作為主要數據上傳通道 (ENABLE_LTE = False)。當 WiFi 可用時，透過標準 HTTPS GET 請求將 LASS 格式感測器數據上傳至雲端。

### WiFi 上傳常數與端點

| 參數名稱 | 常數值 | 說明 |
| :--- | :--- | :--- |
| LASS_REST_URL | https://data.lass-net.org/Upload/MAPS-secure.php | LASS 雲端 REST API 端點 |
| APP_ID | MAPS6 | 應用程式識別碼 |
| DEVICE_ID | (由 /sys/class/net/eth0/address MAC 位址轉換) | 裝置唯一識別碼 |

### LASS 上傳格式欄位對照

上傳訊息以管線分隔 (|) 格式組成，各欄位對照如下：

| LASS 欄位代號 | 對應感測器數據 | 說明 |
| :--- | :--- | :--- |
| s_t0 | TEMP | 環境溫度 (℃) |
| s_h0 | HUMI | 相對濕度 (%RH) |
| s_d0 | PM2.5_AE | 大氣環境 PM2.5 濃度 (μg/m³) |
| s_g8 | CO2 | CO2 濃度 (ppm) |
| s_gg | TVOC | 總揮發性有機物 (ppb) |
| gps_lat | gps_lat | GPS 緯度 (有定位時附加) |
| gps_lon | gps_lon | GPS 經度 (有定位時附加) |
| ver_app | MAPS_PI_VERSION | 樹莓派軟體版本號 |
| date | UTC Date | 上傳時 UTC 日期 |
| time | UTC Time | 上傳時 UTC 時間 |

### 連線判斷與切換邏輯

系統透過 ping www.google.com 判斷 WiFi 是否可用：
* WiFi 可連通 → ConnectionState.WIFI → 使用 HTTPS GET 上傳至 LASS REST API。
* WiFi 不可用且 nbiot_detected 為 True → ConnectionState.NBIOT → 切換至 NB-IoT MQTT 上傳。
* 兩者皆不可用 → ConnectionState.NAN → 暫停上傳，等待下次重試。
* 上傳失敗時，重試間隔縮短為 REUPLOAD_INTERVAL (10 秒)。

## 系統啟動時序與初始化流程

主程式 (system_v7/main.py) 啟動時依序執行以下步驟：

1. 開啟 UART 串口（嘗試 /dev/ttyS0，若失敗則 fallback 至 /dev/ttyAMA0，波特率 115200）。
2. 等待 2 秒等候 MCU 啟動完成。
3. (條件性) 若 ENABLE_LTE = True，初始化 SIM7000E LTE 模組（建立 MAPS6Adapter → SIM7000E_TPC → MQTT 連線物件）。
4. 初始化 Mega2560 MCU，啟用全部 6 大感測器硬體輪詢 (set_sensor_all_polling)。
5. 開啟散熱風扇 (set_fan(True))。
6. 開啟全板 LED 電源 (set_pin_led_all(True)) 並啟動狀態燈 (set_status_led(1))。
7. 同步樹莓派系統時間至 MCU RTC 晶片 (set_rtc_datetime)。
8. 啟動 OLED 顯示背景執行緒 (oled_task)。
9. 啟動 SD 卡寫入背景執行緒 (save_sd_task)。
10. 進入主迴圈，週期性執行感測器讀取、WiFi 檢查、數據上傳。

## 系統排程定時器間隔常數表

| 常數名稱 | 預設值 | 功能說明 |
| :--- | :--- | :--- |
| UPLOAD_INTERVAL | 300 秒 (5 分鐘) | 數據上傳至雲端的週期間隔 |
| GET_SENSOR_DATA_INTERVAL | 5 秒 | MCU 感測器數據輪詢讀取週期 |
| CHECK_WIFI_INTERVAL | 10 秒 | WiFi 連線狀態檢查與 GPS/CSQ 查詢週期 |
| SAVE_SD_INTERVAL | 60 秒 (1 分鐘) | SD 卡 CSV 數據寫入週期 |
| REUPLOAD_INTERVAL | 10 秒 | 上傳失敗後重試等待間隔 |
