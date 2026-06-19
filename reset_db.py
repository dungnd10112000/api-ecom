import os
import sys
import shutil
import subprocess
import time
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("Yeu cau quyen Administrator. Dang tu dong mo cua so Command Prompt voi quyen Admin...")
    # Re-run the script with admin rights
    # sys.executable points to the python binary currently executing this script
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{__file__}"', None, 1)
    sys.exit(0)

# We are running as Administrator now.
pg_dir = r"C:\Program Files\PostgreSQL"
version = "18"
if os.path.exists(pg_dir):
    versions = os.listdir(pg_dir)
    if versions:
        # Use version 18 if available, otherwise take the first found version
        if "18" in versions:
            version = "18"
        else:
            version = sorted(versions, key=lambda x: float(x) if x.replace('.','',1).isdigit() else 0, reverse=True)[0]

data_dir = os.path.join(pg_dir, version, "data")
bin_dir = os.path.join(pg_dir, version, "bin")
psql_path = os.path.join(bin_dir, "psql.exe")
hba_path = os.path.join(data_dir, "pg_hba.conf")
hba_bak_path = os.path.join(data_dir, "pg_hba.conf.bak")

print("=========================================================")
print("  KHOI TAO VA DAT LAI MAT KHAU POSTGRESQL (TCT_CRM)")
print("=========================================================")
print(f"Phien ban PostgreSQL phat hien: {version}")
print(f"Thu muc Data: {data_dir}")
print(f"Duong dan psql: {psql_path}")

service_name = f"postgresql-x64-{version}"

if not os.path.exists(hba_path):
    print(f"LOI: Khong tim thay file cau hinh {hba_path}")
    input("\nNhan Enter de thoat...")
    sys.exit(1)

# Backup pg_hba.conf
shutil.copy2(hba_path, hba_bak_path)
print("[1/6] Da tao file sao luu cho pg_hba.conf.")

try:
    # Modify pg_hba.conf to trust
    with open(hba_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.splitlines()
    new_lines = []
    modified = False
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            parts = stripped.split()
            if len(parts) >= 4 and parts[0] in ("local", "host"):
                # Replace auth method (the last token)
                for auth in ["scram-sha-256", "md5", "password"]:
                    if parts[-1] == auth:
                        parts[-1] = "trust"
                        # Rebuild line by replacing only the last auth method word
                        line = line.replace(auth, "trust")
                        modified = True
                        break
        new_lines.append(line)
        
    with open(hba_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    print("[2/6] Da cau hinh pg_hba.conf sang che do 'trust' (khong mat khau) tam thoi.")
    
    # Restart service to apply trust mode
    print(f"[3/6] Dang dung dich vu {service_name}...")
    subprocess.run(f"net stop {service_name}", shell=True)
    time.sleep(1)
    
    print(f"      Dang khoi dong lai dich vu {service_name}...")
    subprocess.run(f"net start {service_name}", shell=True)
    time.sleep(2)
    
    # Connect and change password
    print("[4/6] Dang ket noi va doi mat khau user 'postgres' thanh '123456'...")
    cmd_alter = [psql_path, "-U", "postgres", "-d", "postgres", "-c", "ALTER USER postgres WITH PASSWORD '123456';"]
    res = subprocess.run(cmd_alter, capture_output=True, text=True)
    if res.returncode == 0:
        print("      -> Doi mat khau thanh cong thanh '123456'!")
    else:
        print("      -> CANH BAO/LOI khi doi mat khau:", res.stderr.strip())
        
    # Check and create database TCT_CRM
    print("[5/6] Dang kiem tra va tao database 'TCT_CRM'...")
    cmd_check_db = [psql_path, "-U", "postgres", "-d", "postgres", "-c", "SELECT 1 FROM pg_database WHERE datname='TCT_CRM';"]
    res_db = subprocess.run(cmd_check_db, capture_output=True, text=True)
    if "1 row" not in res_db.stdout:
        cmd_create = [psql_path, "-U", "postgres", "-d", "postgres", "-c", "CREATE DATABASE TCT_CRM;"]
        res_create = subprocess.run(cmd_create, capture_output=True, text=True)
        if res_create.returncode == 0:
            print("      -> Da tao thanh cong database 'TCT_CRM'!")
        else:
            print("      -> CANH BAO/LOI khi tao database TCT_CRM:", res_create.stderr.strip())
    else:
        print("      -> Database 'TCT_CRM' da ton tai.")

finally:
    # Restore pg_hba.conf
    print("[6/6] Dang khoi phuc lai cau hinh bao mat ban dau cho pg_hba.conf...")
    if os.path.exists(hba_bak_path):
        shutil.copy2(hba_bak_path, hba_path)
        os.remove(hba_bak_path)
        print("      -> Da khoi phuc file pg_hba.conf goc va don dep file sao luu.")
        
    # Restart service again to apply security config
    print(f"      Dang khoi dong lai dich vu {service_name} de ap dung bao mat...")
    subprocess.run(f"net stop {service_name}", shell=True)
    time.sleep(1)
    subprocess.run(f"net start {service_name}", shell=True)
    time.sleep(2)
    print("      -> Dich vu PostgreSQL da hoat dong tro lai o che do bao mat!")
    
    print("\n[Bo sung] Dang tu dong tao cac bang du lieu (tables) trong database 'TCT_CRM'...")
    try:
        # Set database environment variables explicitly to match what was configured
        os.environ["DB_PASSWORD"] = "123456"
        os.environ["DB_NAME"] = "TCT_CRM"
        sys.path.insert(0, os.getcwd())
        from app.database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("      -> Da tao va cau hinh cac bang du lieu thanh cong!")
    except Exception as e:
        print("      -> CANH BAO: Khong the tao cac bang truc tiep qua script (co the do thieu thu vien o moi truong nay).")
        print("                   Hay yen tam, FastAPI se tu tao khi ban khoi dong lai dev server.")
        print(f"                   Chi tiet loi: {e}")

    print("\n>>> HOAN TAT THANH CONG! <<<")
    print("Ung dung FastAPI cua ban da co the ket noi binh thuong voi PostgreSQL.")
    input("\nNhan Enter de ket thuc...")
