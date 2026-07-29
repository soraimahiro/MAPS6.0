# MAPS 6.0 系統硬體模組與 Data 位元對照規範文件 (system.md)

本文件詳細紀錄 MAPS 6.0 樹莓派環境監測盒子中**所有硬體模組**、**Mega2560 MCU 封包 Data 位元對照**、**數值意義**、**控制方式**，以及**新舊系統功能缺漏比對檢查表**。

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

## 2. 盒子內所有模組清單與控制方式細節

### (1) Mega2560 MCU 控制主板
* **硬體功能**：整合所有底層感測器讀取、風扇控制、LED 控制與 RTC 時鐘。
* **控制協定**：UART `/dev/ttyS0` @ 115200 8N1。
* **基本幀結構**：
  `[Leading 0xAA] [Inv_Leading 0x55] [CMD] [Inv_CMD] [DATA...] [Checksum] [Inv_Checksum]`
* **校驗碼計算**：`Checksum = sum(Byte[i] ^ ((i+1)%256)) & 0xFF`

### (2) 散熱風扇 (Cooling Fan)
* **資料位元**：無主動回傳於 Sensor All，可由 `0xBB` (`GET_INFO_PIN_STATE`) 查詢 Pin 狀態。
* **數值意義**：盒內強迫對流散熱。
* **控制方式**：發送指令 `0xC8` (`SET_PIN_FAN_ALL_cmd`)。
  * **金鑰**：`[0x46, 0x41, 0x4E, 0x63]` (`"FANc"`)
  * **狀態參數**：`0x01` (開啟風扇) / `0x00` (關閉風扇)

### (3) SSD1306 OLED 0.96 吋黑白小螢幕
* **控制介面**：I2C 匯流排 (`/dev/i2c-1`，位址 `0x3C`)。
* **控制方式**：由樹莓派直接控制。建立 128x64 黑白點陣圖像畫布（Pillow / Go image），將文字與圖示渲染為點陣陣列後一次性發送至 I2C 顯示。
* **顯示內容**：Device ID, 溫濕度, PM2.5, CO2, TVOC, 網路圖示, 軟體版本。

### (4) SIM7000E LTE / NB-IoT / GPS 模組
* **控制介面**：UART / SPI 轉發介面 + MCU 硬體 Pin 腳控制。
* **控制方式**：
  * MCU 腳位控制：`0xC3` (PwrKey，金鑰 `"NB-I"`), `0xC4` (Sleep Pin，金鑰 `"-IOT"`)。
  * AT 指令集：`AT+CSQ` (訊號品質), `AT+CGNSPWR=1` / `AT+CGNSINF` (GPS 定位與時間), `AT+CNACT` (網路附著)。
* **當前狀態**：可選模組 (`ENABLE_LTE = False` 預設停用，專注於 Wi-Fi 乙太網路)。

### (5) SD 卡擴充與本地備份
* **控制介面**：樹莓派本機檔案系統 (`/home/pi/MAPS6_system/data`)。
* **控制方式**：由主程式建立背景 Thread/Goroutine，每 60 秒依台北本地時間自動將感測器數據寫入以日期命名的 CSV 檔案 (`YYYY-MM-DD.csv`)。

### (6) 狀態指示 LED (Status LED / LED ALL)
* **控制指令**：`0xBC` (`SET_STATUS_LED`) 或 `0xC5` (`SET_PIN_LED_ALL`)。
* **金鑰**：`[0x53, 0x4C, 0x45, 0x44]` (`"SLED"`)。
* **控制意義**：控制盒子外殼上的燈號顏色與閃爍模式。

### (7) Senseair S8 CO2 校正控制
* **控制指令**：`0xC0` (`SET_PIN_CO2_CAL`)。
* **金鑰**：`[0x53, 0x38, 0x4C, 0x50]` (`"S8LP"`)。
* **控制意義**：觸發 Senseair S8 進行大氣 400ppm 零點校正。

### (8) PMS7003 重置與休眠控制
* **控制指令**：`0xC1` (Reset Pin，金鑰 `"PMS3"`), `0xC2` (Set/Sleep Pin，金鑰 `"3003"`)。
* **控制意義**：硬體重置粉塵感測器或切換進睡眠省電模式。

### (9) RTC 即時時鐘 (Real-Time Clock)
* **控制指令**：`0xBA` (`GET_RTC_DATE_TIME`), `0xC7` (`SET_RTC_DATE_TIME`)。
* **控制意義**：將網路 NTP 時間寫入板載 RTC 晶片備份。

---

## 3. 新舊系統功能缺漏比對檢查表 (Missing Feature Checklist)

| 功能 / 模組指令 | 指令碼 (CMD) | 舊版 `box_system` 狀態 | 新版 `new_system` 現狀 | 缺漏評估與建議 |
| :--- | :--- | :--- | :--- | :--- |
| **感測器全讀取 (`GET_SENSOR_ALL`)** | `0xB5` | 已實作 | 已實作 | ✅ 功能完整對齊 |
| **開啟感測器 Polling** | `0xC6` | 已實作 | 已實作 | ✅ 功能完整對齊 |
| **散熱風扇控制 (`SET_PIN_FAN_ALL`)** | `0xC8` | 已實作 | **已修復補回** | ✅ 已於今日補回 `set_fan(True)`，開機自動旋轉 |
| **外殼 LED 指示燈 (`SET_PIN_LED_ALL`)** | `0xC5` / `0xBC` | 已實作 | ⚠️ **缺漏中** | 影響外殼燈號顯示，建議後續補上控制介面 |
| **CO2 大氣校正 (`SET_PIN_CO2_CAL`)** | `0xC0` | 已實作 | ⚠️ **缺漏中** | 需手動校正 CO2 時再調用即可 |
| **PM2.5 重置/休眠 (`SET_PIN_PMS_SET`)** | `0xC1` / `0xC2` | 已實作 | ⚠️ **缺漏中** | 預設持續運作，若需省電休眠可補上 |
| **RTC 時鐘同步 (`SET_RTC_DATE_TIME`)** | `0xC7` | 已實作 | ⚠️ **缺漏中** | 目前直接採用樹莓派本機 Linux 時間 |
