# src/collectors/glama_collector.py

# 注意：这里改用 curl_cffi 的 requests，而不是标准 requests
import curl_cffi
import requests 
import re
import time
import pandas as pd
from tqdm import tqdm
from lxml import html
from config.settings import GITHUB_TOKEN

class GlamaCollector:
    def __init__(self, db_manager):
        self.db = db_manager
        # GitHub API 还是可以用标准头
        self.gh_headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

    def fetch_repo_list_from_awesome(self):
        print("📥 正在读取 Awesome MCP 列表...")
        url = "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/main/README.md"
        try:
            # 这里的 requests 是 curl_cffi.requests
            r = requests.get(url)
            if r.status_code != 200:
                print(f"❌ 无法获取 README: {r.status_code}")
                return []
            
            content = r.text
            pattern = r"github\.com/([a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+)"
            repos = re.findall(pattern, content)
            
            unique_repos = sorted(list(set(repos)))
            unique_repos = [r for r in unique_repos if "awesome" not in r.lower()]
            
            print(f"✅ 发现 {len(unique_repos)} 个 MCP 仓库候选")
            return unique_repos
        except Exception as e:
            print(f"❌ 解析列表失败: {e}")
            return []

    def get_real_tool_count_from_glama(self, repo_full_name):
        """
        爬取 Glama Schema 页面
        URL: https://glama.ai/mcp/servers/@{user}/{repo}/schema
        """
        try:
            user, repo = repo_full_name.split('/')
            target_url = f"https://glama.ai/mcp/servers/@{user}/{repo}/schema"
            r = curl_cffi.requests.get(target_url, impersonate="chrome", timeout=15)
            if r.status_code != 200:
                return None

            # 解析 HTML
            tree = html.fromstring(r.content)
            
            # 使用你指定的 XPath
            xpath_str = '/html/body/div[2]/main/div[1]/div/section[3]/table/tbody/tr'
            rows = tree.xpath(xpath_str)
            tool_count = len(rows)
            print(tool_count)
            
            return tool_count

        except Exception as e:
            # print(f"Error scraping {repo_full_name}: {e}")
            return None

    def get_repo_created_date(self, repo_full_name):
        url = f"https://api.github.com/repos/{repo_full_name}"
        print(url)
        try:
            r = requests.get(url, headers=self.gh_headers)
            if r.status_code == 200:
                return r.json()['created_at'][:10]
            elif r.status_code == 403:
                time.sleep(2)
        except:
            pass
        return None

    def run(self):
        print("🚀 开始执行：Glama 实测爬虫 (使用 Chrome 伪装)...")
        repos = self.fetch_repo_list_from_awesome()[253:264]
        data_rows = []
        print(f"🕷️ 正在分析 {len(repos)} 个仓库...")
        
        for repo in repos:
        # for repo in tqdm(repos):
            tool_count = self.get_real_tool_count_from_glama(repo)
            if tool_count is None:
                continue 
            
            date_str = self.get_repo_created_date(repo)
            if date_str:
                data_rows.append({
                    "date": date_str,
                    "repo": repo,
                    "tool_count": tool_count
                })
            
            time.sleep(0.5) # 稍微快一点，因为 curl_cffi 性能更好

        if not data_rows:
            print("❌ 未获取到数据。")
            return

        # 聚合与保存逻辑
        df = pd.DataFrame(data_rows)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        df_daily = df.groupby('date')['tool_count'].sum().reset_index()
        df_daily['total_skills'] = df_daily['tool_count'].cumsum()
        
        data_to_save = []
        for _, row in df_daily.iterrows():
            d_str = row['date'].strftime('%Y-%m-%d')
            data_to_save.append((d_str, "Available Skills (Tools)", int(row['total_skills'])))
            
        self.db.save_github_data(data_to_save)
        
        # 保存 Servers 计数
        df_servers = df.groupby('date').size().reset_index(name='new_servers')
        df_servers['total_servers'] = df_servers['new_servers'].cumsum()
        server_data = [
            (row['date'].strftime('%Y-%m-%d'), "MCP Servers", int(row['total_servers']))
            for _, row in df_servers.iterrows()
        ]
        self.db.save_github_data(server_data)
        
        print(f"   - 最终 Tools 总数: {df_daily['total_skills'].iloc[-1]}")