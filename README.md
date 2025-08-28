## 每日 GitHub 熱門自動發布（Docker + LLM）

以 Docker 容器每天搜尋新創建且熱門的 GitHub 專案，透過 LLM（Claude 或 Ollama）生成繁中介紹，渲染成 Markdown 後自動提交到指定 repo 分類路徑。支援 GitHub Actions 定時排程與本地 Docker 測試。採用 Docker 隔離以避免影響本機套件環境。

### 功能
- **每日抓取**：使用 GitHub Search API 依星標排序擷取當日新增熱門專案。
- **內容生成**：支援 Claude API 或 Ollama（OpenAI 相容端點）。
- **Markdown 渲染**：以 Jinja2 模板產生清晰的每日精選頁面。
- **自動提交**：透過 GitHub Contents API 將內容提交到目標倉庫指定路徑。

### 快速開始（本地 Docker）
1. 複製環境變數樣板：
   ```bash
   cp env.sample .env
   # 編輯 .env，至少設定 GITHUB_TOKEN、TARGET_REPO
   ```
2. 建置與執行：
   ```bash
   docker build -t daily-tasks:latest .
   # 本地僅輸出檔案（不推送），可先測試 LLM 與模板
   docker run --rm \
     --env-file ./.env \
     -e DRY_RUN=1 \
     -v "$(pwd)/output:/app/output" \
     daily-tasks:latest
   ```
   輸出將在 `output/` 目錄。

### 主要環境變數
- `LLM_PROVIDER`：`claude` 或 `ollama`
- `ANTHROPIC_API_KEY`：使用 Claude 時必填
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`：使用 Ollama 時設定（例：`http://host.docker.internal:11434/v1`）
- `GITHUB_TOKEN`：用於 GitHub API 與提交內容（建議使用 PAT 或 Actions 的內建 token）
- `TARGET_REPO`：目標倉庫（格式：`owner/repo`）
- `TARGET_BRANCH`：目標分支，預設 `main`
- 生成與提交：`MAX_REPOS`、`PATH_PREFIX`、`TIMEZONE`、`COMMIT_AUTHOR_NAME`、`COMMIT_AUTHOR_EMAIL`
- 測試用：`DRY_RUN=1` 僅輸出到容器 `/app/output`

更多參數請見 `env.sample`。

### GitHub Actions 定時排程
倉庫已內建工作流程：`.github/workflows/daily.yml`
- 預設每日 01:05 UTC 執行
- 預設使用 `claude`，請在倉庫 Secrets 設定 `ANTHROPIC_API_KEY`

### 使用 Ollama（可選）
若在本地測試：
```bash
OLLAMA_HOST=127.0.0.1:11434  # 依實際情況
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
export OLLAMA_MODEL=llama3.1:8b-instruct
```
注意：GitHub Actions 無法存取你的本機 Ollama；若要在雲端使用 Ollama，需提供可從 Actions 連線的端點。

### 產出路徑
檔案會依日期寫入：`{PATH_PREFIX}/{YYYY}/{MM}/{YYYY-MM-DD}.md`，例如：`daily/2025/08/2025-08-28.md`。

### 專案結構
```
app/
  main.py            # 主流程：抓取 → 生成 → 渲染 → 提交
  config.py          # 設定載入
  github/            # GitHub API 互動（搜尋、內容提交）
  llm/               # LLM 供應商抽象與實作（Claude, Ollama）
  render.py          # Jinja2 模板渲染
templates/
  daily.md.j2
.github/workflows/daily.yml
Dockerfile
requirements.txt
```

### 疑難排解
- 搜尋/速率限制：請確保 `GITHUB_TOKEN` 可用，否則 API 限速很快用盡。
- LLM 解析失敗：若模型未回傳合法 JSON，程式會回退為專案描述避免中斷。
- Ollama 通訊：請確認 `OLLAMA_BASE_URL` 正確且容器可連線（本機通常用 `host.docker.internal`）。


