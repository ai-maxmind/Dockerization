import configparser, os, sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import get_current_context
from airflow.decorators import task
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from modules import Utils, FTPServer, OracleDB
from pendulum import timezone
local_tz = timezone("Asia/Ho_Chi_Minh")


def loadConfig():
    config = configparser.ConfigParser()
    config.read(Utils.findConfigFile("env.ini"))
    return config


def exportQueryResults(db, queries, prefix="DS") -> list:
    today = datetime.now().strftime("%d%m%Y")
    files = []

    for sql, suffix in queries:
        df = db.executeSQL(sql, returnResult=True)
        if df is None or df.empty:
            print(f"⚠️ No data for {suffix}")
            continue

        filename = f"{prefix}_Retry_{suffix}_{today}.xlsx"
        df.to_excel(filename, index=False)
        print(f"✅ Exported file: {filename}")
        files.append(filename)

    return files


@task
def extractFromOracle() -> list:
    cfg = loadConfig()
    db = OracleDB(cfg["crm_db"])
    db.connectDB()
    db.runProcedure("PCK_CSKH_SMS.SMS_RETRY")
    queries = [
        (
        """
        SELECT DISTINCT ISDN,
               CODE,
               TO_CHAR(EXPIRE_DATETIME, 'DD/MM/YYYY HH24:MI') AS NGAY,
               TO_CHAR(GIA_GOI_SMS, 'FM999G999G999', 'NLS_NUMERIC_CHARACTERS='',.''') || 'd' AS GIA_GOI_SMS,
               UU_DAI_CODAU
        FROM LICHSU_RETRY
        WHERE NGAYDULIEU = TRUNC(SYSDATE)
              AND NHOM = 'MBF'
        ORDER BY NGAY ASC
        """,
        "MBF",
        ),
        (
        """
        SELECT DISTINCT ISDN,
               CODE,
               TO_CHAR(EXPIRE_DATETIME, 'DD/MM/YYYY HH24:MI') AS NGAY,
               TO_CHAR(GIA_GOI_SMS, 'FM999G999G999', 'NLS_NUMERIC_CHARACTERS='',.''') || 'd' AS GIA_GOI_SMS,
               UU_DAI_CODAU
        FROM LICHSU_RETRY
        WHERE NGAYDULIEU = TRUNC(SYSDATE)
              AND NHOM = 'MEE'
        ORDER BY NGAY ASC
        """,
        "MEE",
        )
    ]
    return exportQueryResults(db, queries)


@task
def uploadFilesToFTP(files: list):
    context = get_current_context()
    ti = context['ti']
    todayStr = datetime.now().strftime("%Y%m%d")

    alreadyRenewFileUploaded = ti.xcom_pull(key=f"uploaded_{todayStr}", task_ids="uploadFilesToFTP")
    if alreadyRenewFileUploaded:
        print("⚠️ Uploaded today, skip it.")
        return

    if not files:
        print("⚠️ There are no files to upload.")
        return

    cfg = loadConfig()
    ftp = FTPServer(cfg["ftp_server4"])
    ftp.connectFTP()
    remoteDir = "/SingleCycle_retry_campaign"

    for file in files:
        if not os.path.exists(file):
            print(f"⚠️ File does not exist: {file}")
            continue
        try:
            ftp.uploadFile(file, remoteDir)
            os.remove(file)
            print(f"🗑️ Local file deleted: {file}")
        except Exception as e:
            print(f"❌ Error uploading {file}: {e}")


    ti.xcom_push(key=f"uploaded_{todayStr}", value=True)

defaultArgs = {
    "owner": "mobifone",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="RetryDataToFTPDaily",
    default_args=defaultArgs,
    description="Dữ liệu retry gói cước",
    schedule_interval="0 14 * * *",
    start_date=datetime(2025, 1, 1, tzinfo=local_tz),
    catchup=False,
    tags=["oracle", "ftp", "excel"],
) as dag:

    files = extractFromOracle()
    uploadFilesToFTP(files)
