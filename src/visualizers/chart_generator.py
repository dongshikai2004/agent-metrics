import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, LogLocator
from adjustText import adjust_text # 关键库
import os

class ChartGenerator:
    def __init__(self):
        os.makedirs("output", exist_ok=True)
        # 设置更专业的绘图风格
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['font.family'] = 'sans-serif'

    def format_tokens(self, x, pos):
        """格式化 Token 数量显示"""
        if x >= 1000000:
            return f'{int(x/1000000)}M'
        elif x >= 1000:
            return f'{int(x/1000)}k'
        return int(x)

    def generate_comparison_chart(self, df_tools, df_models):
        fig, ax1 = plt.subplots(figsize=(16, 10))

        # 颜色定义
        color_ctx = '#2ca02c' # 绿色系代表 Context
        color_tool = '#d62728' # 红色系代表 Tools/Ecosystem
        
        # ==========================================
        # 1. 绘制 Context Window (散点 + 标签) - 左轴
        # ==========================================
        ax1.set_xlabel('Timeline', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Context Window Size (Tokens)', color=color_ctx, fontsize=16, fontweight='bold')
        
        # 绘制散点
        # 区分 Milestone (大点) 和 普通 HF 模型 (小点)
        milestones = df_models[df_models['downloads'] == -1]
        others = df_models[df_models['downloads'] > -1]
        print(df_models)
        # 画背景小点 (HF Top Models)
        ax1.scatter(others['created_at'], others['context_length'], 
                   color=color_ctx, alpha=0.3, s=30, label='Open Source Models')
        
        # 画关键里程碑大点
        ax1.scatter(milestones['created_at'], milestones['context_length'], 
                   color=color_ctx, alpha=1.0, s=100, edgecolor='white', linewidth=2, zorder=5, label='Key Milestones')

        # 趋势线 (为了看清走势，连接里程碑的最大值)
        # 提取外包络线
        max_line = df_models.set_index('created_at').resample('Q')['context_length'].max().fillna(method='ffill')
        ax1.plot(max_line.index, max_line.values, color=color_ctx, alpha=0.2, linestyle='--', linewidth=2)

        # 设置对数坐标
        ax1.set_yscale('log')
        ax1.yaxis.set_major_formatter(FuncFormatter(self.format_tokens))
        ax1.tick_params(axis='y', labelcolor=color_ctx, labelsize=12)

        # --- 智能添加标签 (最重要的一步) ---
        texts = []
        for _, row in milestones.iterrows():
            # 格式化日期以便绘图
            texts.append(ax1.text(row['created_at'], row['context_length'], 
                                  f"  {row['model_id']} ({self.format_tokens(row['context_length'],0)})", 
                                  fontsize=10, color='#1b5e20', fontweight='bold'))
        for _, row in others.iterrows():
            # 格式化日期以便绘图
            texts.append(ax1.text(row['created_at'], row['context_length'], 
                                  f"  {row['model_id']} ({self.format_tokens(row['context_length'],0)})", 
                                  fontsize=10, color='#1b5e20', fontweight='bold'))
        # 使用 adjust_text 自动避让重叠
        # arrowprops=dict(arrowstyle='-', color='gray', alpha=0.5) 会自动画出指向线
        adjust_text(texts, ax=ax1, 
                    arrowprops=dict(arrowstyle='->', color='gray', lw=0.5),
                    time_lim=1) # 限制计算时间，防止卡死

        # ==========================================
        # 2. 绘制 Tools/Skills Growth (曲线) - 右轴
        # ==========================================
        ax2 = ax1.twinx()
        ax2.set_ylabel('AI Ecosystem Activity (GitHub Repos)', color=color_tool, fontsize=16, fontweight='bold')
        
        # 绘制平滑曲线
        sns.lineplot(data=df_tools, x='date', y='repo_count', ax=ax2, 
                     color=color_tool, linewidth=4, label='Tools & Agents Growth')
        
        # 填充颜色增加视觉冲击力
        ax2.fill_between(df_tools['date'], df_tools['repo_count'], color=color_tool, alpha=0.1)
        print(df_tools)
        ax2.tick_params(axis='y', labelcolor=color_tool, labelsize=12)
        # 这里可以选择是否用对数轴。如果增长极快（指数级），建议也用 log
        # ax2.set_yscale('log') 

        # ==========================================
        # 3. 装饰与保存
        # ==========================================
        plt.title('The Scaling Gap: Context Window vs. Ecosystem Capabilities', fontsize=20, pad=20, fontweight='bold')
        
        # 合并图例
        handles1, labels1 = ax1.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        # 过滤重复项
        by_label = dict(zip(labels1 + labels2, handles1 + handles2))
        ax1.legend(by_label.values(), by_label.keys(), loc='upper left', frameon=True, fontsize=12, shadow=True)

        # 设置X轴日期格式
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.xticks(rotation=45)

        plt.tight_layout()
        save_path = "output/detailed_model_comparison.png"
        plt.savefig(save_path, dpi=300)
        print(f"✨ 高级图表已生成: {save_path}")
        plt.show()