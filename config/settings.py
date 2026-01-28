import os
import dotenv
dotenv.load_dotenv()

# API Tokens
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN_HERE") 
HUGGINGFACE_TOKEN = os.getenv("HF_TOKEN", "") # 可选，主要用于更高配额

# 爬取的时间范围（按季度采样，减少API请求次数）
START_DATE = "2022-01-01"
END_DATE = "2026-01-01"
FREQ = "3ME" # 3 Month End

# 数据库路径
DB_PATH = "data/ecosystem.db"