from src.database.db_manager import DBManager
from src.collectors.tools_collector import GlamaCollector
from src.collectors.huggingface_collector import HuggingFaceCollector
from src.processors.data_cleaner import DataProcessor
from src.visualizers.chart_generator import ChartGenerator
from config.milestones import MILESTONE_MODELS # 导入手动数据
# import os

def main():
    # os.environ["http_proxy"] = "http://127.0.0.1:10808"
    # os.environ["https_proxy"] = "http://127.0.0.1:10808"
    db = DBManager()
    # --- 1. 注入数据 ---
    print("--- Step 1: Injecting Milestone Data ---")
    # db.save_milestones(MILESTONE_MODELS) # 注入 GPT-4 等数据

    print("--- Step 2: Running Collectors ---")
    # 爬取 GitHub 数据
    gh = GlamaCollector(db)
    gh.run()
    
    # 爬取 HuggingFace 数据 (补充背景点)
    hf = HuggingFaceCollector(db)
    hf.run()

    # --- 2. 处理与绘图 ---
    print("\n--- Step 3: Visualization ---")
    processor = DataProcessor(db)
    df_tools, df_models = processor.get_plotting_data()

    visualizer = ChartGenerator()
    visualizer.generate_comparison_chart(df_tools, df_models)

if __name__ == "__main__":
    main()