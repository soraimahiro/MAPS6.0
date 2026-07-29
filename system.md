# MAPS 6.0 系統硬體模組與 Data 位元對照規範文件

本文件詳細紀錄 MAPS 6.0 樹莓派環境監測盒子中**所有硬體模組**、**Mega2560 MCU 封包 Data 位元對照**、**數值意義**、**控制方式**、**金鑰防護機制**、**雙重 SD 儲存架構**、**GPS/LTE 運作機制**與**新舊系統功能比對**。

---

## 1. Mega2560 MCU 協定與 `GET_SENSOR_ALL` (0xB5) Data 位元對照表

Mega2560 MCU 透過 UART (`/dev/ttyS0` @ 115200 8N1) 定時或被動回應感測器數據。
當發送 `0xB5` (`GET_SENSOR_ALL`) 指令時，MCU 回傳共 48 Bytes 封包（包含 4 碼 Header + 42 碼 Payload Data + 2 碼 Checksum）。

下表為 **42 Bytes Payload Data** 的完整位元對照：

| 數據 Payload 位元 (Bytes) | 封包位元 (data[N]) | 模組 / 感測器名稱 | 欄位代號 | 數值計算與數據意義 | 單位 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Bytes [0:2]** | `data[2:4]` | SHT3x 溫濕度感測器 | `TEMP` | `int16 / 100.0` (環境溫度) | ℃ |
| **Bytes [2:4]** | `data[4:6]` | SHT3x 溫濕度感測器 | `HUMI` | `int16 / 100.0` (相對濕度) | %RH |
| **Bytes [4:6]** | `data[6:8]` | Senseair S8 CO2 感測器 | `CO2` | `uint16` (65535 代表無回應/初始化中, 建議轉換為 -1) | ppm |
| **Bytes [6:8]** | `data[8:10]` | Senseair S8 CO2 感測器 | `AVE_CO2` | `uint16` (平均 CO2 濃度) | ppm |
| **Bytes [8:10]** | `data[10:12]` | Sensirion SGP30 有機物 | `TVOC` | `uint16` (總揮發性有機化合物) | ppb |
| **Bytes [10:12]** | `data[12:14]` | Sensirion SGP30 有機物 | `eCO2` | `uint16` (等效 CO2 估算值) | ppm |
| **Bytes [12:14]** | `data[14:16]` | Sensirion SGP30 有機物 | `S_H2` | `uint16` (原始氫氣 Raw 訊號值) | Raw |
| **Bytes [14:16]** | `data[16:18]` | Sensirion SGP30 有機物 | `S_ETHANOL` | `uint16` (原始乙醇 Raw 訊號值) | Raw |
| **Bytes [16:18]** | `data[18:20]` | Sensirion SGP30 有機物 | `BASELINE_TVOC` | `uint16` (TVOC 校正基準值) | Raw |
| **Bytes [18:20]** | `data[20:22]` | Sensirion SGP30 有機物 | `BASELINE_eCO2` | `uint16` (eCO2 校正基準值) | Raw |
| **Bytes [20:22]** | `data[22:24]` | TCS34725 / AS7262 照度 | `Illuminance` | `uint16` (環境光照強度) | Lux |
| **Bytes [22:24]** | `data[24:26]` | TCS34725 / AS7262 色溫 | `Color_Temperature` | `uint16` (環境色溫) | °K |
| **Bytes [24:26]** | `data[26:28]` | 光學色彩感測器 | `CH_R` | `uint16` (紅色光 Raw 通道) | Raw |
| **Bytes [26:28]** | `data[28:30]` | 光學色彩感測器 | `CH_G` | `uint16` (綠色光 Raw 通道) | Raw |
| **Bytes [28:30]** | `data[30:32]` | 光學色彩感測器 | `CH_B` | `uint16` (藍色光 Raw 通道) | Raw |
| **Bytes [30:32]** | `data[32:34]` | 光學色彩感測器 | `CH_C` | `uint16` (全光譜 Clear Raw 通道) | Raw |
| **Bytes [32:34]** | `data[34:36]` | PMS7003 懸浮微粒感測器 | `PM1.0_AE` | `uint16` (大氣環境 PM1.0 濃度) | μg/m³ |
| **Bytes [34:36]** | `data[36:38]` | PMS7003 懸浮微粒感測器 | `PM2.5_AE` | `uint16` (大氣環境 PM2.5 濃度) | μg/m³ |
| **Bytes [36:38]** | `data[38:40]` | PMS7003 懸浮微粒感測器 | `PM10.0_AE` | `uint16` (大氣環境 PM10 濃度) | μg/m³ |
| **Bytes [38:40]** | `data[40:42]` | PMS7003 懸浮微粒感測器 | `PM1.0_SP` | `uint16` (標準顆粒 PM1.0 濃度) | μg/m³ |
| **Bytes [40:42]** | `data[42:44]` | PMS7003 懸浮微粒感測器 | `PM2.5_SP` | `uint16` (標準顆粒 PM2.5 濃度) | μg/m³ |
| **Bytes [42:44]** | `data[44:46]` | PMS7003 懸浮微粒感測器 | `PM10.0_SP` | `uint16` (標準顆粒 PM10 濃度) | μg/m³ |

---

## 2. 硬體模組控制規範與安全金鑰分析

### (1) 指令金鑰 (Command Key) 防護機制分析
MCU 對於部分控制指令要求隨附 4 Bytes 的驗證金鑰（例如 CO2 校正 `"S8LP"`、風扇 `"FANc"`、指示燈 `"SLED"`、PMS 重置 `"PMS3"`）：
* **防範串口雜訊誤觸**：樹莓派開關機或硬體拔插時，串口 (`/dev/ttyS0`) 腳位可能產生隨機電位雜訊。要求金鑰驗證可確保雜訊不會誤觸風扇關閉或硬體重置。
* **保護硬體記憶體與校正參數**：CO2 校正與重置會寫入感測器 Flash/EEPROM。驗證金鑰可防止非預期的誤操作覆蓋校正基準。

---

### (2) 散熱風扇模組 (Cooling Fan)
* **控制指令**：`0xC8` (`SET_PIN_FAN_ALL_cmd`)
* **金鑰**：`[0x46, 0x41, 0x4E, 0x63]` (`"FANc"`)
* **狀態參數**：`0x01` (開啟風扇) / `0x00` (關閉風扇)
* **控制意義**：控制盒子內部的散熱風扇強制對流。新版已實作開機自動調用 `set_fan(True)` 啟動風扇。

---

### (3) 外殼狀態指示燈號 (Status LED / LED ALL)
* **控制指令**：
  * `0xBC` (`SET_STATUS_LED`)：狀態指示燈。`State = 0` (關閉), `State = 1` (恆亮 ON，代表開機正常), `State = 2 ~ 65534` (呼吸燈閃爍週期 ms，代表網路連線/資料傳送中)。
  * `0xC5` (`SET_PIN_LED_ALL`)：全板 LED 開關（金鑰 `[0x53, 0x4C, 0x45, 0x44]` `"SLED"`）。`State = 1` (開啟全燈), `State = 0` (關閉全燈/夜間暗房模式)。

---

### (4) CO2 校正與 PMS7003 重置運作規範
* **Senseair S8 CO2 校正 (`0xC0`)**：
  * **金鑰**：`[0x53, 0x38, 0x4C, 0x50]` (`"S8LP"`)
  * **執行規範**：僅在人工維護保養、且確定設備置於戶外大氣 (400 ppm CO2) 環境中時由維護人員手動發起。**嚴禁定時自動執行**，避免在高 CO2 室內誤將高濃度校正為 400 ppm。
* **PMS7003 重置與休眠 (`0xC1` / `0xC2`)**：
  * **金鑰**：`"PMS3"` (Reset) / `"3003"` (Set/Sleep)
  * **執行規範**：當感測器讀數連續卡死無回應時執行硬體 Reset (`0xC1`)；或需要延長雷射晶片壽命時切換至省電休眠 (`0xC2`)。

---

### (5) 雙重 SD 卡儲存架構分析 (Dual SD Architecture)
系統設計包含兩層獨立的 SD 卡儲存層級：
1. **樹莓派系統主卡 (`/dev/mmcblk0`)**：安裝 Linux OS，並寫入本機備份目錄 `/home/pi/MAPS6_system/data`。
2. **訂製擴充板 SPI SD 卡槽 (`/dev/mmcblk2p1` / `/mnt/SD`)**：經由 SPI0 匯流排獨立連接於擴充板上，支援離線脫機備份。即使樹莓派系統損壞，拔下擴充板上的 SD 卡即可直接救回歷史 CSV 數據。

---

### (6) GPS / LTE 模組運作機制與演進
* **硬體整合**：GPS 衛星接收器整合於 Simcom SIM7000E (LTE-M/NB-IoT + GNSS) 晶片中。
* **SIM 卡獨立性**：GPS 衛星定位為單向接收衛星訊號，**完全不需要 SIM 卡與 4G 流量**。發送 `AT+CGNSPWR=1` 開啟天線電源即可獨立完成定位。
* **新舊系統演進**：
  * **舊版 `box_system`**：並未調用硬體 GPS，而是在配置檔 `PI_test_config.py` 中靜態寫死硬編碼經緯度 (`25.1933, 121.787`)。
  * **新版 `new_system`**：預留了呼叫 SIM7000E 動態 GPS 定位與 CSQ 訊號查詢之介面。

---

## 3. 新舊系統功能缺漏比對檢查表 (Missing Feature Checklist)

| 功能 / 模組指令 | 指令码 (CMD) | 舊版 `box_system` 狀態 | 新版 `new_system` 現狀 | 缺漏評估與建議 |
| :--- | :--- | :--- | :--- | :--- |
| **感測器全讀取 (`GET_SENSOR_ALL`)** | `0xB5` | 已實作 | 已實作 | ✅ 功能完整對齊 |
| **開啟感測器 Polling** | `0xC6` | 已實作 | 已實作 | ✅ 功能完整對齊 |
| **散熱風扇控制 (`SET_PIN_FAN_ALL`)** | `0xC8` | 已實作 | **已補回實作** | ✅ 已補回 `set_fan(True)`，開機自動旋轉散熱 |
| **外殼 LED 指示燈 (`SET_PIN_LED_ALL`)** | `0xC5` / `0xBC` | 已實作 | **已補回實作** | ✅ 已補回 `set_status_led(1)` 與 `set_pin_led_all(True)` 燈號控制 |
| **CO2 大氣校正 (`SET_PIN_CO2_CAL`)** | `0xC0` | 已實作 | **已補回實作** | ✅ 已補回 `set_co2_calibration()` 手動校正介面 |
| **PM2.5 重置與休眠 (`SET_PIN_PMS_SET`)** | `0xC1` / `0xC2` | 已實作 | **已補回實作** | ✅ 已補回 `set_pms_reset()` 與 `set_pms_sleep()` 重置/休眠介面 |
| **RTC 時鐘寫入 (`SET_RTC_DATE_TIME`)** | `0xC7` | 已實作 | **已補回實作** | ✅ 已補回 `set_rtc_datetime()` 硬體時鐘同步功能 |
