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

@task
def renewalList():
    cfg = loadConfig()
    db = OracleDB(cfg["crm_db"])
    db.connectDB()
    db.runProcedure("PCK_CSKH_SMS.DAILY_RENEWAL_LIST")
defaultArgs = {
    "owner": "mobifone",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="DailyRenewalListTask",
    default_args=defaultArgs,
    description="Dữ liệu gia hạn gói dài kỳ",
    schedule_interval="50 13 * * *",
    start_date=datetime(2025, 1, 1, tzinfo=local_tz),
    catchup=False,
    tags=["oracle", "ftp", "excel"],
) as dag:
    renewalList()
