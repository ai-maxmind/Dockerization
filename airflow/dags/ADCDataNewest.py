import configparser, os, sys, gzip, traceback, time
from datetime import datetime, timedelta
from ftplib import error_perm, error_temp, error_proto, error_reply
from airflow import DAG
from airflow.decorators import task
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from modules import Utils, FTPServer, OracleDB
from pendulum import timezone
local_tz = timezone("Asia/Ho_Chi_Minh")


def loadConfig():
    config = configparser.ConfigParser()
    config.read(Utils.findConfigFile("env.ini"))
    return config


def downloadLatestADC(cfg, remoteDir, localDir, days=3):
    ftp = None
    try:
        ftp = FTPServer(cfg)
        ftp.connectFTP()

        for i in range(days):
            date_str = (datetime.today() - timedelta(i)).strftime('%Y%m%d')
            filename = f"ADC_UPDATE_{date_str}.txt.gz"
            local_path = os.path.join(localDir, filename)

            try:
                success = ftp.downloadFile(remoteDir, filename, localDir)
                if success:
                    print(f"✅ Downloaded: {filename}")
                    return local_path
            except (error_perm, error_temp, error_proto, error_reply) as ftp_err:
                print(f"⚠️ FTP error while downloading {filename}: {ftp_err}")
            except FileNotFoundError:
                print(f"⚠️ File not found on server: {filename}")
            except Exception as e:
                print(f"❌ Unexpected error for {filename}: {e}")

        return "⚠️ No matching file in last days"

    except ConnectionError as conn_err:
        print(f"❌ Connection error: {conn_err}")
        return f"❌ Connection error: {conn_err}"
    except TimeoutError:
        print("❌ Timeout while connecting to FTP server")
        return "❌ Timeout while connecting to FTP server"
    except Exception as e:
        print(f"❌ Unexpected top-level error: {e}")
        return f"❌ Unexpected error: {e}"
    finally:
        if ftp:
            try:
                ftp.disconnectFTP()
                print("🔌 FTP connection closed.")
            except Exception as close_err:
                print(f"⚠️ Error closing FTP connection: {close_err}")
    

@task
def downloadADCDaily():
    try:
        print("🚀 Starting ADC daily download...", flush=True)

        cfg = loadConfig()
        if not cfg or "ftp_server1" not in cfg:
            raise ValueError("Missing or invalid configuration: 'ftp_server1' not found")

        remoteDir = "/all/ADC"
        localDir = "downloads"

        filePath = downloadLatestADC(cfg["ftp_server1"], remoteDir, localDir)

        if not filePath or "⚠️" in str(filePath):
            print("⚠️ No matching file found in last days.", flush=True)
            return None

        print(f"✅ Successfully downloaded file: {filePath}", flush=True)
        return filePath

    except FileNotFoundError as fnf_err:
        print(f"❌ File not found error: {fnf_err}", flush=True)
        traceback.print_exc()
        return None

    except ConnectionError as conn_err:
        print(f"❌ Connection error while downloading ADC: {conn_err}", flush=True)
        traceback.print_exc()
        return None

    except TimeoutError as timeout_err:
        print(f"❌ Timeout during ADC download: {timeout_err}", flush=True)
        traceback.print_exc()
        return None

    except ValueError as val_err:
        print(f"❌ Configuration or parameter error: {val_err}", flush=True)
        traceback.print_exc()
        return None

    except Exception as e:
        print(f"💥 Unexpected error during ADC download: {e}", flush=True)
        traceback.print_exc()
        return None

    finally:
        print(f"🕒 Task finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)


@task(execution_timeout=timedelta(minutes=120))
def importADCData(filePath: str, batchSize: int = 1000000, taskId: str = "adc_import_task"):
    startTime = time.time()
    db = None

    try:
        print("🚀 Starting ADC data import...", flush=True)
        if not filePath or not os.path.exists(filePath):
            raise FileNotFoundError(f"ADC_UPDATE file not found: {filePath}")

        cfg = loadConfig()
        db = OracleDB(cfg["crm_db"])
        db.connectDB()

        table = "ADC_UPDATE"
        requiredCols = ["ISDN", "IMSI", "DEVICE_CATEGORY", "DATA_2G", "DATA_3G", "DATA_3GP", "DATA_4G", "DATA_5G"]
        indexList = [("IDX_ADC_UPDATE", ["ISDN", "IMSI"])]

        checkpointFile = Utils.getCheckpointFileName(taskId, filePath)
        db.checkpointFile = checkpointFile

        if os.path.exists(checkpointFile):
            lastIndex = db.loadCheckpoint()
            print(f"📍 Found checkpoint file. Resuming from line: {lastIndex:,}", flush=True)
        else:
            lastIndex = 0
            print("⚠️ No checkpoint found. Starting fresh import.", flush=True)

        if lastIndex == 0:
            print("🗑️ Dropping indexes before import...", flush=True)
            for idxName, _ in indexList:
                try:
                    db.dropIndex(idxName)
                except Exception as e:
                    print(f"⚠️ Could not drop index {idxName}: {e}", flush=True)

            print(f"🧹 Truncating table {table}...", flush=True)
            db.truncateTable(table)

        total, batch, currentLine = 0, [], 0

        with gzip.open(filePath, "rt", encoding="utf-8", errors="ignore") as f:
            header_line = f.readline().strip()
            if not header_line:
                raise ValueError("Empty or missing header line in file")

            headerRaw = header_line.split("|")
            header = [col.strip().upper() for col in headerRaw]
            headerMap = {col: i for i, col in enumerate(header)}

            availableCols = [c for c in requiredCols if c in headerMap]
            missingCols = [c for c in requiredCols if c not in headerMap]

            print(f"📄 Header detected: {headerRaw}", flush=True)
            if missingCols:
                print(f"⚠️ Missing columns: {missingCols}", flush=True)
            print(f"✅ Using columns: {availableCols}", flush=True)

            for lineNo, line in enumerate(f, start=2):
                if lineNo <= lastIndex:
                    continue 

                try:
                    parts = line.strip().split("|")
                    if len(parts) < 2:
                        continue

                    row = {
                        col: (parts[headerMap[col]][:38] if col == "DATA_3GP" else parts[headerMap[col]])
                        if headerMap[col] < len(parts)
                        else ""
                        for col in availableCols
                    }

                    batch.append(row)
                    currentLine = lineNo

                    if len(batch) >= batchSize:
                        db.insertData(table, availableCols, batch)
                        db.saveCheckpoint(currentLine)
                        total += len(batch)
                        elapsed = time.time() - startTime
                        startLine = currentLine - len(batch) + 1  
                        print(f"✅ {filePath}: Imported lines {startLine:,} → {currentLine:,} ({total/elapsed:,.1f} rows/s, total {total:,})",flush=True)

                        batch.clear()

                except Exception as e:
                    print(f"⚠️ Error at line {lineNo}: {e}", flush=True)
                    traceback.print_exc()
                    db.saveCheckpoint(currentLine)
                    break  

        if batch:
            db.insertData(table, availableCols, batch)
            total += len(batch)
            db.saveCheckpoint(currentLine)

        elapsed = time.time() - startTime
        print(f"🎉 Finished importing {total:,} rows in {elapsed:,.1f}s ({total/elapsed:,.1f} rows/s)", flush=True)
        # db.clearCheckpoint()

        try:
            os.remove(filePath)
            print(f"🗑️ Deleted local file: {filePath}", flush=True)
        except Exception as e:
            print(f"⚠️ Could not delete file: {e}", flush=True)

        print("⚡ Recreating indexes...", flush=True)
        for idxName, idxCols in indexList:
            try:
                db.createIndex(idxName, table, idxCols)
            except Exception as e:
                print(f"⚠️ Could not recreate index {idxName}: {e}", flush=True)

        db.closeDB()
        print("✅ All tasks completed successfully.", flush=True)
        return True

    except Exception as e:
        print(f"💥 Import failed: {e}", flush=True)
        traceback.print_exc()
        if db:
            try:
                db.rollbackConnection()
            except:
                pass
        return False


defaultArgs = {
    "owner": "mobifone",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="ADCDataNewest",
    default_args=defaultArgs,
    description="Import dữ liệu ADC gần nhất",
    schedule_interval="0 10 * * *",
    start_date=datetime(2025, 1, 1, tzinfo=local_tz),
    catchup=False,
    max_active_runs=1,
    tags=["oracle", "ftp", "excel"],
) as dag:

    filePath = downloadADCDaily()
    importADCData(filePath)
