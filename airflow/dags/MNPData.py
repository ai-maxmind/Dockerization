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
def mnpData():
    cfg = loadConfig()
    db = OracleDB(cfg["crm_db"])
    db.connectDB()
    db.runProcedure("SP_BC_MNP")
    db.runProcedure("SP_PROCESS_MNP")
defaultArgs = {
    "owner": "mobifone",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="MNPData",
    default_args=defaultArgs,
    description="Dữ liệu MNP mỗi ngày",
    schedule_interval="0 8 * * *",
    start_date=datetime(2025, 1, 1, tzinfo=local_tz),
    catchup=False,
    tags=["oracle", "ftp", "excel"],
) as dag:

    mnpData()
