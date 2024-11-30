import os
from . import config
import sqlite3

def bootup():
    # 데이터베이스 연결 생성 (없으면 생성됨)
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))

    # 커서 객체 생성
    cursor = conn.cursor()

    # 'user' 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            userid TEXT PRIMARY KEY,
            money INTEGER DEFAULT 0,
            IsBlack BOOLEAN DEFAULT 0,
            last_received INTEGER DEFAULT 0
        )
    ''')

    # 'server' 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS server (
            srvid TEXT PRIMARY KEY
        )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS baccarat_results
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     result CHAR(1) NOT NULL)
    ''')

    # 변경사항 저장
    conn.commit()

    # 연결 닫기
    conn.close()