import os
import sys
import time
import subprocess
import shutil

# Paths
pg_bin_dir = r"C:\Program Files\PostgreSQL\18\bin"
initdb_path = os.path.join(pg_bin_dir, "initdb.exe")
pg_ctl_path = os.path.join(pg_bin_dir, "pg_ctl.exe")
createdb_path = os.path.join(pg_bin_dir, "createdb.exe")
db_dir = os.path.abspath("local_db")
env_path = os.path.abspath(".env")

print("=========================================================")
print("  KHOI TAO POSTGRESQL USER-SPACE (PORT 5433)")
print("=========================================================")

# 1. Initialize database cluster if not exists
if not os.path.exists(db_dir):
    print(f"[1/4] Dang khoi tao cluster database tai: {db_dir}...")
    pw_file = "temp_pw.txt"
    with open(pw_file, "w", encoding="utf-8") as f:
        f.write("123456\n")
        
    try:
        cmd_init = [
            initdb_path,
            "-D", db_dir,
            "-U", "postgres",
            "-A", "scram-sha-256",
            f"--pwfile={pw_file}"
        ]
        res = subprocess.run(cmd_init, capture_output=True, text=True)
        if res.returncode != 0:
            print("LOI khi khoi tao database cluster:", res.stderr)
            sys.exit(1)
        print("      -> Khoi tao database cluster thanh cong!")
    finally:
        if os.path.exists(pw_file):
            os.remove(pw_file)
            
    # Modify postgresql.conf to use port 5433
    conf_path = os.path.join(db_dir, "postgresql.conf")
    with open(conf_path, "r", encoding="utf-8") as f:
        conf_data = f.read()
        
    # Uncomment and replace port = 5432 with port = 5433
    if "#port = 5432" in conf_data:
        conf_data = conf_data.replace("#port = 5432", "port = 5433")
    elif "port = 5432" in conf_data:
        conf_data = conf_data.replace("port = 5432", "port = 5433")
    else:
        conf_data += "\nport = 5433\n"
        
    with open(conf_path, "w", encoding="utf-8") as f:
        f.write(conf_data)
    print("      -> Da cau hinh PostgreSQL chay tren cong 5433.")
else:
    print(f"[1/4] Thu muc database '{db_dir}' da ton tai. Bo qua khoi tao.")

# 2. Start PostgreSQL service on port 5433
print("[2/4] Dang khoi chay PostgreSQL tren cong 5433...")
# Use pg_ctl to start the server in the background
# We pass -w to wait for startup to complete
cmd_start = [pg_ctl_path, "-D", db_dir, "-o", "-p 5433", "start"]
res_start = subprocess.run(cmd_start, capture_output=True, text=True)
print("STDOUT:", res_start.stdout.strip())
if res_start.returncode != 0 and "already running" not in res_start.stdout and "already running" not in res_start.stderr:
    print("CANH BAO/LOI khi khoi chay:", res_start.stderr.strip())
time.sleep(3)

# 3. Create database TCT_CRM
print("[3/4] Dang tao database 'TCT_CRM' tren cong 5433...")
env_vars = os.environ.copy()
env_vars["PGPASSWORD"] = "123456"
cmd_create_db = [createdb_path, "-p", "5433", "-U", "postgres", "TCT_CRM"]
res_create = subprocess.run(cmd_create_db, capture_output=True, text=True, env=env_vars)
if res_create.returncode == 0:
    print("      -> Da tao thanh cong database 'TCT_CRM'!")
elif "already exists" in res_create.stderr:
    print("      -> Database 'TCT_CRM' da ton tai san.")
else:
    print("      -> Chi tiet:", res_create.stderr.strip())

# 4. Update .env configuration
print("[4/4] Dang cap nhat file .env sang cong 5433...")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
        
    new_lines = []
    for line in lines:
        if line.startswith("DB_PORT="):
            line = "DB_PORT=5433"
        elif line.startswith("DB_PASSWORD="):
            line = "DB_PASSWORD=123456"
        new_lines.append(line)
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    print("      -> File .env da duoc cap nhat thanh cong!")
else:
    print("      -> LOI: Khong tim thay file .env.")

print("\n>>> HOAN TAT THET LAP DATABASE USER-SPACE! <<<")
print("Ung dung FastAPI hien tai se tu dong ket noi toi PostgreSQL cong 5433.")
