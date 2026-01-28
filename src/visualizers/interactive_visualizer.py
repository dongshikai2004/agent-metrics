import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os

class InteractiveChartGenerator:
    def __init__(self):
        os.makedirs("output", exist_ok=True)

    def format_tokens(self, x):
        """将数值格式化为 1M, 128k 等"""
        if x >= 1000000:
            return f'{round(x/1000000, 1)}M'
        elif x >= 1000:
            return f'{int(x/1000)}k'
        return str(x)

    def prepare_tools_data_with_details(self, df_gh):
        """
        处理工具数据：不仅计算总和，还准备 hover 时的细分详情
        """
        # 1. 确保日期格式
        df_gh['date'] = pd.to_datetime(df_gh['date'])
        
        # 2. 透视表：行=日期，列=Topic，值=数量
        df_pivot = df_gh.pivot_table(index='date', columns='topic', values='repo_count', aggfunc='sum').fillna(0)
        
        # 3. 计算总和
        df_pivot['Total'] = df_pivot.sum(axis=1)
        
        # 4. 构建 Hover 详情字符串
        # 格式: "Total: 100<br>LangChain: 60<br>AutoGen: 40"
        hover_texts = []
        for index, row in df_pivot.iterrows():
            # 按数量降序排列，取前5个展示，避免列表太长
            top_contributors = row.drop('Total').sort_values(ascending=False).head(5)
            
            detail_str = f"<b>📅 {index.strftime('%Y-%m-%d')}</b><br>"
            detail_str += f"<b>Total Ecosystem Repos: {int(row['Total'])}</b><br>"
            detail_str += "------------------<br>"
            
            for topic, count in top_contributors.items():
                if count > 0:
                    detail_str += f"{topic}: {int(count)}<br>"
            
            hover_texts.append(detail_str)
            
        return df_pivot.index, df_pivot['Total'], hover_texts

    def generate_html_chart(self, df_gh, df_models):
        """生成交互式 HTML 文件"""
        
        # --- 1. 创建双轴图表 ---
        fig = make_subplots(
            specs=[[{"secondary_y": True}]], # 启用双Y轴
            subplot_titles=("AI Evolution: Context vs. Skills",)
        )

        # ==========================================================
        # 左轴：Context Window (散点图)
        # ==========================================================
        
        # A. 分离数据
        milestones_closed = df_models[df_models['downloads'] == -1]
        milestones_open = df_models[df_models['downloads'] > 0]
        background_models = df_models[df_models['downloads'] > 0]

        # B. 辅助函数：生成模型 Hover 信息
        def create_model_hover(row):
            t = "Closed" if row['downloads'] == -1 else "Open Source"
            if row['downloads'] > 0: t = "HuggingFace Model"
            return (
                f"<b>🤖 {row['model_id']}</b><br>"
                f"📅 Release: {row['created_at'].strftime('%Y-%m-%d')}<br>"
                f"🧠 Context: <b>{self.format_tokens(row['context_length'])}</b> Tokens<br>"
                f"🏷️ Type: {t}"
            )

        # C. 绘制背景模型 (灰色小点)
        fig.add_trace(
            go.Scatter(
                x=background_models['created_at'],
                y=background_models['context_length'],
                mode='markers',
                name='Other Models',
                marker=dict(color='gray', size=5, opacity=0.3),
                text=[create_model_hover(r) for _, r in background_models.iterrows()],
                hoverinfo='text'
            ),
            secondary_y=False
        )

        # D. 绘制闭源模型 (蓝色大圆点)
        fig.add_trace(
            go.Scatter(
                x=milestones_closed['created_at'],
                y=milestones_closed['context_length'],
                # mode='markers+text', # 显示文字
                mode='markers', # 显示文字
                name='Closed Source (GPT/Gemini)',
                text=milestones_closed['model_id'], # 直接显示名字
                textposition="top center",
                marker=dict(color='#1f77b4', size=12, line=dict(width=2, color='white')),
                textfont=dict(size=10, color='#1f77b4'),
                hovertext=[create_model_hover(r) for _, r in milestones_closed.iterrows()],
                hoverinfo='text'
            ),
            secondary_y=False
        )

        # E. 绘制开源模型 (绿色菱形)
        fig.add_trace(
            go.Scatter(
                x=milestones_open['created_at'],
                y=milestones_open['context_length'],
                # mode='markers+text',
                mode='markers',
                name='Open Source (Llama/Mistral)',
                text=milestones_open['model_id'],
                textposition="bottom center",
                marker=dict(symbol='diamond', color='#2ca02c', size=12, line=dict(width=2, color='white')),
                textfont=dict(size=10, color='#2ca02c'),
                hovertext=[create_model_hover(r) for _, r in milestones_open.iterrows()],
                hoverinfo='text'
            ),
            secondary_y=False
        )

        # ==========================================================
        # 右轴：Tools Growth (折线图)
        # ==========================================================
        
        # 准备带详情的数据
        dates, total_counts, hover_details = self.prepare_tools_data_with_details(df_gh)

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=total_counts,
                mode='lines',
                name='AI Ecosystem Growth',
                line=dict(color='#d62728', width=4), # 红色粗线
                hovertext=hover_details, # 关键：这里放入了 LangChain 等细分数据
                hoverinfo='text'
            ),
            secondary_y=True
        )

        # ==========================================================
        # 样式与布局设置
        # ==========================================================
        
        # 设置 Y 轴类型 (对数轴)
        fig.update_yaxes(title_text="Context Window (Tokens)", type="log", secondary_y=False, showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxes(title_text="Total Ecosystem Repos", type="linear", secondary_y=True, showgrid=False) # 工具数量可以用线性或对数，视增长爆发程度而定

        # 设置 X 轴
        fig.update_xaxes(title_text="Timeline", showgrid=True)

        # 整体布局
        fig.update_layout(
            title_text="<b>The AI Gap:</b> Model Context vs. Ecosystem Capabilities",
            title_font_size=24,
            hovermode="closest", # 鼠标靠近哪里显示哪里
            template="plotly_white",
            height=800, # 高度
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            font=dict(family="Arial, sans-serif")
        )

        # 导出
        output_path = "output/interactive_ecosystem_chart.html"
        fig.write_html(output_path)
        print(f"✨ 交互式图表已生成: {output_path}")
        print("👉 请在浏览器中打开该文件查看。")