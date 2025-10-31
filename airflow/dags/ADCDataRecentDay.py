import configparser, os, sys, time, traceback, glob, gzip, csv
from datetime import datetime, timedelta
import pandas as pd, numpy as np
from airflow import DAG
from airflow.decorators import task
from pendulum import timezone
from ftplib import all_errors as FTP_ERRORS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from modules import Utils, FTPServer, OracleDB


local_tz = timezone("Asia/Ho_Chi_Minh")


def loadConfig():
    config = configparser.ConfigParser()
    config.read(Utils.findConfigFile("env.ini"))
    return config


def deleteFile(filePath, fileName):
    if os.path.exists(filePath):
        for file in glob.glob(os.path.join(filePath, fileName)):
            try:
                os.remove(file)
                print(f"Deleted file: {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")


def downloadADC7Files(cfg, remoteDir, localDir, days=9, count=7):
    ftp = FTPServer(cfg)
    downloaded, found = [], 0
    maxRetries = 3

    try:
        ftp.connectFTP()
    except Exception as e:
        print(f"[ERROR] Không thể kết nối FTP ban đầu: {e}")
        return None

    for i in range(1, days + 1):
        if found >= count:
            break

        dateStr = (datetime.today() - timedelta(days=i)).strftime("%Y%m%d")
        fname = f"ADC_UPDATE_{dateStr}.txt.gz"
        filePath = os.path.join(localDir, fname)

        for attempt in range(1, maxRetries + 1):
            try:
                ok = ftp.downloadFile(remoteDir, fname, localDir)
                if ok:
                    downloaded.append(filePath)
                    found += 1
                    print(f"[INFO] ✅ Đã tải thành công {fname}")
                    break

                else:
                    print(f"[WARN] ⚠️ Tải thất bại {fname} (lần {attempt}/{maxRetries})")
                    time.sleep(3)

            except FTP_ERRORS as fe:
                print(f"[FTP ERROR] ❌ Lỗi FTP khi tải {fname}: {fe}")
                try:
                    ftp.disconnectFTP()
                    time.sleep(2)
                    ftp.connectFTP()
                    print("[INFO] 🔄 Đã reconnect FTP thành công")
                except Exception as reconnect_err:
                    print(f"[CRITICAL] 🚫 Không thể reconnect FTP: {reconnect_err}")
                    break 

            except (OSError, IOError) as io_err:
                print(f"[IO ERROR] 💾 Lỗi ghi file {fname}: {io_err}")
                break

            except Exception as e:
                print(f"[UNKNOWN ERROR] ⚡ Lỗi không xác định khi tải {fname}: {e}")
                print(f"↳ Loại lỗi: {type(e).__name__}")
                break

        else:
            print(f"[WARN] 🚫 Bỏ qua {fname} sau {maxRetries} lần thất bại")

    try:
        ftp.disconnectFTP()
    except Exception as e:
        print(f"[WARN] ⚠️ Lỗi khi ngắt kết nối FTP: {e}")

    print(f"✅ Tổng số file tải thành công: {found}/{count}")
    return downloaded if downloaded else None

def safeInt(val):
    try:
        return int(str(val).strip())
    except:
        return 0


def streamADCFile(filePath, filePattern, batchSize=10000):
    files = sorted(glob.glob(os.path.join(filePath, filePattern)), reverse=True)
    if not files:
        print("[WARN] ❗ Không tìm thấy file nào khớp với pattern.")
        return

    latest = files[0]
    otherFiles = files[1:]

    allISDN = set()
    isdnWith3G4G5G = set()

    for f in otherFiles:
        print(f"[INFO] 🔍 Xử lý file phụ: {f}", flush=True)
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fp:
                reader = csv.DictReader(fp, delimiter='|')
                for row in reader:
                    isdn = row.get("isdn")
                    if not isdn:
                        continue
                    allISDN.add(isdn)
                    d3 = safeInt(row.get("data_3g", 0))
                    d4 = safeInt(row.get("data_4g", 0))
                    d5 = safeInt(row.get("data_5g", 0))
                    if d3 > 0 or d4 > 0 or d5 > 0:
                        isdnWith3G4G5G.add(isdn)
        except Exception as e:
            print(f"[WARN] ⚠️ Bỏ qua file phụ {f}: {e}")

    only2gSet = allISDN - isdnWith3G4G5G
    del allISDN, isdnWith3G4G5G  

    print(f"[INFO] 📥 Đang stream file chính: {latest}")
    batch = []

    try:
        with gzip.open(latest, 'rt', encoding='utf-8') as fp:
            reader = csv.DictReader(fp, delimiter='|')
            for row in reader:
                d2 = safeInt(row.get("data_2g", 0))
                d3 = safeInt(row.get("data_3g", 0))
                d4 = safeInt(row.get("data_4g", 0))
                d5 = safeInt(row.get("data_5g", 0))
                volte = safeInt(row.get("volte", 0))

                isdn = row.get("isdn", "")
                only2G = int(isdn in only2gSet and d3 == 0 and d4 == 0 and d5 == 0)


                batch.append({
                    "isdn": isdn,
                    "imei": row.get("imei", ""),
                    "device_category": row.get("device_category", ""),
                    "data_2g": d2,
                    "data_3g": d3,
                    "data_4g": d4,
                    "data_5g": d5,
                    "volte": volte,
                    "only_2g": only2G
                })

                if len(batch) >= batchSize:
                    yield batch
                    batch = []

            if batch:
                yield batch

    except Exception as e:
        print(f"[CRITICAL] 🚨 Lỗi tổng thể: {e}")

    print("[INFO] ✅ Đã kết thúc streamADCFile_batches.")

def runStep(name, func, *a, **kw):
    t0 = time.perf_counter()
    print(f"{name} ...")
    r = func(*a, **kw)
    print(f"{name} OK ({time.perf_counter() - t0:.2f}s)")
    return r


@task
def importADCData():
    start = time.perf_counter()
    print("=== START import ADC Data ===")
    try:
        cfg = runStep("Load config", loadConfig)
        ftp, db_cfg = cfg["ftp_server1"], cfg["crm_db"]
        if not (ftp and db_cfg):
            print("❌ Missing cfg")
            return False

        runStep("Download files", downloadADC7Files, ftp, "/all/ADC", "downloads")
        db = runStep("Connect DB", OracleDB, db_cfg)
        db.connectDB()

        runStep("Drop index", db.dropIndex, "ADC_DATA_INDEX")
        runStep("Delete old", db.truncateTable, "ADC_DATA")

        for batch in streamADCFile("downloads", "ADC_UPDATE_*.txt.gz"):
            if batch:
                db.insertData(
                    "ADC_DATA",
                    ['isdn','imei','device_category','data_2g','data_3g','data_4g','data_5g','only_2g','volte'],
                    batch
                )

        runStep("Create index", db.createIndex, "ADC_DATA_INDEX", "ADC_DATA", ["ISDN"])
        runStep("Close DB", db.closeDB)
        runStep("Cleanup", deleteFile, "downloads", "ADC_UPDATE_*.txt.gz")

        print(f"✅ Done in {time.perf_counter() - start:.2f}s")
        return True

    except Exception as e:
        print(f"❌ {e}\n{traceback.format_exc()}")
        return False
    finally:
        print("=== END importADCData ===\n")


defaultArgs = {
    "owner": "mobifone",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="ADCDataRecentDay",
    default_args=defaultArgs,
    description="Import dữ liệu ADC trong 7 ngày gần nhất",
    schedule_interval="0 0 * * *",   
    start_date=datetime(2025, 9, 25, tzinfo=local_tz),
    catchup=False,
    tags=["oracle", "ftp", "excel"],
) as dag:
    importADCData()
