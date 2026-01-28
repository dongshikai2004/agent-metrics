import pandas as pd

class DataProcessor:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_plotting_data(self):
        # --- 1. GitHub 数据 (Tools) ---
        df_gh = self.db.get_github_data()
        df_gh['date'] = pd.to_datetime(df_gh['date'])
        # 累加所有 Topic 的数量
        df_tools = df_gh.groupby('date')['repo_count'].sum().reset_index().sort_values('date')

        # --- 2. Model 数据 (Context) ---
        df_model = self.db.get_model_data()
        df_model['created_at'] = pd.to_datetime(df_model['created_at'])
        
        # 过滤无效数据
        df_model = df_model[(df_model['context_length'] > 0) & (df_model['context_length'] <= 10000000)]
        
        # 区分：关键里程碑 vs 普通爬取数据
        # 约定：downloads = -1 是我们在 milestones.py 里定义的关键模型
        df_milestones = df_model[df_model['downloads'] == -1].copy()
        
        # 另外提取 HF 上下载量最高的前 50 个模型作为背景散点（避免图太乱）
        df_hf_top = df_model[df_model['downloads'] > 0].sort_values('downloads', ascending=False).head(50)
        
        # 合并用于画散点
        # df_scatter = pd.concat([df_milestones, df_hf_top])
        df_scatter = pd.concat([df_model, df_hf_top])

        # 这里的 df_scatter 包含了具体的模型名称和长度，用于画点和标签
        # df_tools 用于画另一条曲线
        return df_tools, df_scatter