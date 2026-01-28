import requests
from tqdm import tqdm
from config.settings import HUGGINGFACE_TOKEN
from config.keywords import HF_KEYWORDS

class HuggingFaceCollector:
    def __init__(self, db_manager):
        self.db = db_manager
        self.headers = {}
        if HUGGINGFACE_TOKEN:
            self.headers["Authorization"] = f"Bearer {HUGGINGFACE_TOKEN}"

    def fetch_model_info(self):
        """
        从 HF API 获取热门模型列表，并尝试解析其 context length
        """
        print("🚀 开始采集 Hugging Face 模型 Context 数据...")
        
        # 获取热门模型 (按下载量排序，取前200个，以此作为代表)
        params = {
            "sort": "downloads",
            "direction": "-1",
            "limit": 200,
            "filter": "text-generation" # 仅关注文本生成模型
        }
        
        try:
            url = "https://huggingface.co/api/models"
            r = requests.get(url, headers=self.headers, params=params)
            models = r.json()
            
            cleaned_data = []
            
            for model in tqdm(models, desc="Analyzing Models"):
                model_id = model['modelId']
                created_at = model.get('createdAt', '2022-01-01')[:10] # 截取日期
                downloads = model.get('downloads', 0)
                
                # 获取 Config 文件以确定 Context Window
                context_length = self.get_context_length(model_id)
                
                if context_length:
                    cleaned_data.append((model_id, created_at, context_length, downloads))
            
            self.db.save_model_data(cleaned_data)
            print(f"✅ 成功采集 {len(cleaned_data)} 个模型的 Context 信息")
            
        except Exception as e:
            print(f"HF Collection Error: {e}")

    def get_context_length(self, model_id):
        """
        尝试读取 config.json 中的 max_position_embeddings 或类似字段
        """
        try:
            config_url = f"https://huggingface.co/{model_id}/resolve/main/config.json"
            r = requests.get(config_url, headers=self.headers, timeout=5)
            if r.status_code == 200:
                config = r.json()
                # 常见的 context key
                keys = ['max_position_embeddings', 'seq_length', 'n_positions', 'max_sequence_length', 'context_length']
                for k in keys:
                    if k in config:
                        return config[k]
                # 有些模型如 Mistral 使用 sliding window，这里做简单处理
                if 'sliding_window' in config and config['sliding_window']:
                     return config['sliding_window']
            print(model_id)
            return None
        except:
            print(model_id)
            return None

    def run(self):
        self.fetch_model_info()