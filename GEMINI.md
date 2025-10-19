# Gemini Agent 專案工具鏈說明

本文件指導 Agent 運行環境的配置、工具串接機制，以及 Agent 可調用的功能。

## 新增專案需求：家用智能管家

**專案目標：** 家用智能管家

**核心需求：**
1. **即時監控與控制：** 即時讀取並監控當前各個 client (amb82, ESP32) 的溫度，同時可以反向控制 client 處理指定的行為。
2. **任務管理：** 可將待辦事項設為 task 逐步處理，並透過 Google Task 進行管理（見下方說明）。
3. **版本控制：** 透過 GitHub 做版控（見下方說明）。
4. **程式碼結構：** 各 client 的程式碼應另外創一個資料夾存放，避免資料放同一個根目錄造成混淆。

### 伺服器 (Server) 程式規格：
* **硬體/系統：** 一般 PC，作業系統 Windows。
* **視覺化程式：** 需有個視覺化程式可動態顯示當前各 client 的數值。若有異常數值，則需標記（例如：溫度超過閾值）。

### 用戶端 (Client) 規格：
| Client | 晶片 | 核心功能 |
| :--- | :--- | :--- |
| **Client amb82** | amb82 | 1. 讀取 DHT11 溫度並回傳給 Server。 2. **紅外線 (IR) 遙控器學習功能**：掛載 IR Receiver，接收到訊號後回傳給 Server 儲存，Server 儲存到對應按鍵。Server 點擊按鍵後，要求 client amb82 發送儲存的 IR 訊號。 |
| **Client ESP32** | ESP32 | 讀取 DHT11 溫度並回傳給 Server。 |

---

## 1. GitHub 認證 (Patrol Access Token, PAT)

- **用途：** 用於 Agent 執行自動化的程式碼庫操作（Clone, Pull, Push, Issue/PR 管理），**並用於管家專案的版控。**
- **認證機制：** 採用 **PAT (Personal Access Token)**，透過安全的環境變數傳遞。
- **變數名稱：** `GITHUB_PAT`
- **使用指南：**
    1. Agent 程式碼必須讀取 `os.environ.get("GITHUB_PAT")` 來獲取令牌。
    2. 在呼叫 GitHub REST API 時，將令牌用於 `Authorization: token <PAT>` Header 中。
    3. 在 Git 命令列操作時，需依賴 **Git 憑證管理器 (GCM)** 記住此 PAT。

### 🚀 GitHub PAT 連線測試與驗證需求

Agent 必須執行以下操作來驗證串接：

1. **環境變數檢查：** 確保環境中已設定 `GITHUB_PAT` 變數。
2. **API 測試：** 呼叫 GitHub API 嘗試**讀取**目標儲存庫資訊，並嘗試**創建**一個測試 Issue。
3. **錯誤處理：** 若返回 401/403 錯誤，應提示使用者檢查 PAT 是否過期或權限（Scope）是否足夠。

---

## 2. NotebookLM (知識提取與上下文提供 - 需手動介入)

- **用途：** 專案文件知識的檢索與摘要。作為 Agent 專案的事實依據（Grounding Context）。
- **認證機制：** 無 API，純粹的 **資料流程 (Data Flow)** 串接。
- **Agent 限制：** Agent **無法**自動上傳文件或發起查詢。
- **Agent 行動指南：**
    1. **要求：** Agent 需要專案規範或背景知識時，應要求使用者手動在 NotebookLM 中完成知識摘要。
    2. **輸入：** 使用者將 NotebookLM 產生的**摘要/筆記**，以文字或本地檔案 (`@file.md`) 的形式提供給 Agent。
    3. **處理：** Agent 依賴自身內建的 **RAG 能力**，將手動提供的內容作為**一次性、高權重的事實上下文**來進行推理和程式碼生成。

---

## 3. Google Task (任務管理串接 - 透過 OAuth 2.0)

- **用途：** 讓 Agent 自動在 Google Task 中創建、更新、完成或查詢專案任務，**特別是用於管理智能管家專案中的待辦事項 (Tasks)。**
- **認證機制：** 採用 **OAuth 2.0** 流程。
- **核心目標：** 獲取並安全儲存一個**刷新令牌 (Refresh Token)**。

### 初始設置步驟 (需要人工初始化)

Agent 應在首次運行時指導使用者完成以下步驟：

1. **Google Cloud 設定：** 建立專案、啟用 **Google Tasks API**，並建立 **OAuth 2.0 用戶端 ID**。
2. **一次性授權：**
    * 使用者需運行一個初始化腳本，產生**授權 URL**，並手動在瀏覽器中完成授權。
    * 授權完成後，Agent 程式碼會接收並將取得的 **Refresh Token** 儲存至本地文件 (例如：`google_task_token.json`)。

### Agent 自動化行為

1. **存取：** Agent 每次需要互動時，都會載入本地儲存的 Refresh Token。
2. **刷新：** Agent 使用 Refresh Token **自動**換取新的 Access Token。
3. **操作：** Agent 使用 Access Token 呼叫 Google Tasks REST API 執行任務操作。

---

## 4. Agent 工具定義 (Tools for Automated Operations)

為了讓 Agent 能主動執行 GitHub 和 Google Task 的相關操作，以下定義了 Agent 可調用的功能。Agent 在接收到任務時，應根據任務內容判斷是否需要呼叫這些工具。

### 4.1 GitHub 工具

- **工具名稱範例：** `github_issue_creator`, `github_repo_reader`, `github_committer`
- **功能描述：**
    * `create_github_issue(title: str, body: str, labels: list = None)`: 在指定儲存庫創建一個新的 Issue。
    * `read_repo_info()`: 獲取指定儲存庫的基本資訊。
    * `clone_repository(repo_url: str, local_path: str)`: 將 GitHub 儲存庫克隆到本地。
    * `commit_and_push_changes(local_path: str, message: str, branch: str)`: 將本地變更提交並推送到 GitHub 儲存庫。
- **觸發條件 (Agent 應主動使用時機)：** 當任務明確要求「創建問題」、「更新程式碼」、「同步儲存庫」等。

### 4.2 Google Task 工具

- **工具名稱範例：** `google_task_manager`
- **功能描述：**
    * `create_google_task(title: str, due_date: str = None, notes: str = None, task_list_id: str = 'default')`: 在 Google Task 中創建一個新任務。
    * `list_google_tasks(task_list_id: str = 'default', completed: bool = False)`: 列出指定任務清單中的任務。
    * `complete_google_task(task_id: str, task_list_id: str = 'default')`: 完成一個 Google Task。
- **觸發條件 (Agent 應主動使用時機)：** 當任務明確要求「新增待辦事項」、「查看任務進度」、「完成某項任務」等。

---

## 5. 新增需求：家用智能管家 Server 視覺化程式

Agent 需要開發一個應用程式作為智能管家專案的核心伺服器 (Server)，負責數據接收、狀態顯示與發送控制命令。

### 程式規格 (Server)：

1. **語言/框架：** Python (優先) + 輕量級 Web 或桌面 GUI 框架 (如 Flask/Streamlit/Tkinter)。
2. **作業系統：** Windows (主要)。
3. **通訊協議：** 建議採用 MQTT 或 WebSocket 實現即時、雙向的數據交換。
    * **Server 行為：** 接收 Client 的溫度數據；發送 IR 碼發射請求。
    * **Client 行為：** 發送 DHT11 溫度；發送 IR 碼學習結果。
4. **核心功能：**

#### 4.1 數據顯示與監控
* **Client 連線狀態：** 實時顯示 `amb82` 和 `ESP32` 的連線狀態 (線上/離線)。
* **溫度面板：** 為每個 Client 創建一個專屬面板，實時顯示最新的 **DHT11 溫度**。
* **異常警示：**
    * 允許使用者設定溫度上限閾值 (例如 $30^\circ\text{C}$)。
    * 若任一 Client 回傳的溫度超過閾值，該數值或面板應**標記為紅色**或閃爍警示。

#### 4.2 遙控器學習與控制介面 (針對 Client amb82)
* **學習模式按鈕：**
    * 視覺化介面需有一個按鈕，點擊後向 `amb82` 發送進入 **IR 學習模式**的請求。
    * 介面應顯示「等待接收 IR 訊號中...」。
* **IR 碼儲存：**
    * 介面需有設定區，允許使用者定義多組**按鍵名稱** (例如: `TV_POWER`, `AC_COOL_26`)。
    * 當 `amb82` 回傳學習到的 IR 原始碼時，Server 應將其與使用者當前選擇的按鍵名稱**關聯並儲存** (建議儲存為 JSON 或 SQLite)。
* **控制發射：**
    * 介面應提供一個按鍵區，顯示所有已儲存的按鍵名稱。
    * 使用者點擊任一按鍵，Server 應**發送對應的 IR 碼**給 `amb82`，要求其發射訊號。

### Agent 執行結果：
* Agent 應提供 Server 程式碼的**架構設計**與**核心功能實現程式碼** (例如：Websocket/MQTT 數據接收與處理邏輯)。
* 提供執行程式碼和安裝依賴的詳細步驟 (例如：所需的 Python 庫和運行環境配置)。