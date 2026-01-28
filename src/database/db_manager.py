import sqlite3
import pandas as pd
from config.settings import DB_PATH
import os

class DBManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # 存储 GitHub 工具数量快照
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS github_stats (
                date TEXT,
                topic TEXT,
                repo_count INTEGER,
                PRIMARY KEY (date, topic)
            )
        ''')
        # 存储模型 Context 信息
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_context_stats (
                model_id TEXT PRIMARY KEY,
                created_at TEXT,
                context_length INTEGER,
                downloads INTEGER
            )
        ''')
        self.conn.commit()

    def save_github_data(self, data_list):
        cursor = self.conn.cursor()
        cursor.executemany(
            'INSERT OR REPLACE INTO github_stats VALUES (?, ?, ?)',
            data_list
        )
        self.conn.commit()

    def save_model_data(self, data_list):
        cursor = self.conn.cursor()
        cursor.executemany(
            'INSERT OR REPLACE INTO model_context_stats VALUES (?, ?, ?, ?)',
            data_list
        )
        self.conn.commit()

    def get_github_data(self):
        return pd.read_sql("SELECT * FROM github_stats", self.conn)

    def get_model_data(self):
        return pd.read_sql("SELECT * FROM model_context_stats", self.conn)
    
    def save_milestones(self, milestones):
        """
        保存手动定义的里程碑数据
        milestones: list of tuples (name, date, context)
        """
        cursor = self.conn.cursor()
        # 我们复用 model_context_stats 表，但把 downloads 设为 -1 以标记为手动数据
        data_to_insert = [
            (name, date, context, -1) 
            for name, date, context in milestones
        ]
        cursor.executemany(
            'INSERT OR REPLACE INTO model_context_stats VALUES (?, ?, ?, ?)',
            data_to_insert
        )
        self.conn.commit()