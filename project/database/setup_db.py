import os
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from supabase import create_client, Client

def setup_database():
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not db_url:
        print("Error: DATABASE_URL 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 1. schema.sql 실행
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                cur.execute(f.read())
            print("스키마(schema.sql) 생성 완료.")
        else:
            print("경고: schema.sql 파일을 찾을 수 없습니다.")

        # 2. seed.sql 실행
        seed_path = os.path.join(os.path.dirname(__file__), 'seed.sql')
        if os.path.exists(seed_path):
            with open(seed_path, 'r', encoding='utf-8') as f:
                cur.execute(f.read())
            print("초기 데이터(seed.sql) 삽입 완료.")
        else:
            print("경고: seed.sql 파일을 찾을 수 없습니다.")

        # 3. 기본 관리자 계정 생성
        admin_id = 'admin'
        admin_pw = 'admin1234'
        admin_nickname = '관리자'
        admin_role = 'ADMIN'
        
        # 관리자 계정이 이미 존재하는지 확인
        cur.execute("SELECT id FROM users WHERE user_id = %s", (admin_id,))
        if cur.fetchone() is None:
            pw_hash = generate_password_hash(admin_pw)
            cur.execute(
                "INSERT INTO users (user_id, password_hash, nickname, role) VALUES (%s, %s, %s, %s)",
                (admin_id, pw_hash, admin_nickname, admin_role)
            )
            print(f"관리자 계정 생성 완료. (ID: {admin_id}, PW: {admin_pw})")
        else:
            print("관리자 계정이 이미 존재합니다.")

        conn.commit()
        cur.close()
        conn.close()
        print("데이터베이스 초기화 성공!")
        
        if supabase_url and supabase_key:
            print("Supabase 스토리지 버킷 세팅을 시작합니다...")
            supabase: Client = create_client(supabase_url, supabase_key)
            
            buckets = supabase.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            
            if 'posts' not in bucket_names:
                supabase.storage.create_bucket('posts', options={"public": True})
                print("스토리지 버킷('posts') 자동 생성 완료!")
            else:
                print("스토리지 버킷('posts')이 이미 존재합니다.")
        else:
            print("경고: SUPABASE_URL 또는 SUPABASE_KEY가 없어 스토리지를 세팅하지 못했습니다.")
        
    except Exception as e:
        print(f"데이터베이스 초기화 중 오류 발생: {e}")

if __name__ == '__main__':
    setup_database()
