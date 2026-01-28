import os
import sys
import webbrowser
from src.database.db_manager import DBManager
from src.processors.data_cleaner import DataProcessor
from src.visualizers.interactive_visualizer import InteractiveChartGenerator

def main():
    print("==========================================")
    print("   AI Ecosystem Visualization Launcher    ")
    print("==========================================")

    # 1. 检查数据库是否存在
    db_path = "data/ecosystem.db"
    if not os.path.exists(db_path):
        print(f"❌ 错误: 数据库文件 {db_path} 不存在。")
        print("请先运行 'python main.py' 进行数据采集。")
        return

    # 2. 连接数据库
    print("1. Loading data from database...")
    db = DBManager()

    # 3. 获取数据
    # A. 获取 GitHub 原始数据 (用于展示工具细分详情)
    df_gh_raw = db.get_github_data()
    
    if df_gh_raw.empty:
        print("❌ 错误: GitHub 数据为空。请检查爬虫是否成功运行。")
        return

    # B. 获取模型数据 (经过 Processor 处理，包含里程碑标记)
    processor = DataProcessor(db)
    # 我们只需要 df_models，不需要 processor 处理过的 tools 数据(因为我们要自己处理细分)
    _, df_models = processor.get_plotting_data()

    # if df_models.empty:
    #     print("❌ 错误: 模型数据为空。")
    #     return

    print(f"   - Loaded {len(df_gh_raw)} GitHub records")
    print(f"   - Loaded {len(df_models)} Model records")

    # 4. 生成交互式图表
    print("2. Generating interactive HTML chart...")
    viz = InteractiveChartGenerator()
    
    # 这里的 generate_html_chart 需要引用上一条回复中的 interactive_visualizer.py 代码
    viz.generate_html_chart(df_gh_raw, df_models)

    # 5. 自动打开浏览器
    output_file = os.path.abspath("output/interactive_ecosystem_chart.html")
    print(f"3. Opening in browser: {output_file}")
    
    try:
        webbrowser.open(f"file://{output_file}")
    except Exception as e:
        print(f"⚠️ 无法自动打开浏览器，请手动打开文件: {output_file}")

if __name__ == "__main__":
    main()