from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum, configparser, sys, os, pandas as pd, math
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules import Utils, OracleDB, FTPServer

VNtimezone = pendulum.timezone('Asia/Ho_Chi_Minh')

def readFile(path, file):
    try:
        df = pd.read_csv(path, encoding='utf-8')
        df['FILENAME'], df['INSERTDATE'], df['FILEDATE'] = file, datetime.now().date(), datetime.strptime(file.split("_")[-1].split(".")[0], '%Y%m%d').date()
        data = df.to_dict(orient='records')
        for r in data:
            for k, v in r.items():
                if isinstance(v, float) and math.isnan(v): r[k] = None
            for k in ['DATETIME_UPDATE', 'DATETIME_INDB']:
                if isinstance(r.get(k), str):
                    try: r[k] = datetime.strptime(r[k], "%m/%d/%Y %I:%M:%S %p")
                    except: r[k] = None
        return data
    except pd.errors.EmptyDataError:
        print(f"⚠️ Empty file: {file}")
        return None

def importDataMobifiberTask(**kwargs):
    cfg = configparser.ConfigParser()
    cfg.read(Utils.findConfigFile("env.ini"))
    db = OracleDB(cfg["bos_db"])
    db.connectDB()
    ftp = FTPServer(cfg["ftp_server3"])
    ftp.connectFTP()
    fname = f"CSG_FTTX_{(datetime.now()-timedelta(days=1)).strftime('%Y%m%d')}.csv"
    ftp.downloadFile('/CTY8/FTTX', fname, './downloads/')

    header = ['DATETIME_ID','REGION','PROVINCE','DVT','TVT','DISTRICT','TYPE','NAME','ADDRESS','LONGITUDE','LATITUDE','LOAI','USER_UPDATE','DATETIME_INDB','DATETIME_UPDATE','TONG_SO_PORT_QUANG_1G_TRONG','STATUS','FILENAME','INSERTDATE','FILEDATE']
    for f in ftp.files:
        fp = os.path.join('./downloads', f)
        rows = readFile(fp, f)
        if rows:
            db.deleteData('MOBIFIBER_RESOURCES', f"FILENAME = '{f}'")
            db.insertData('MOBIFIBER_RESOURCES', header, rows)
            print(f"✅ {len(rows)} rows inserted")
        os.remove(fp)
    db.closeDB()

with DAG(
    'importDataMobifiberTask',
    schedule_interval='0 8 * * *',
    start_date=pendulum.datetime(2025, 8, 1, tz=VNtimezone),
    catchup=False,
    dagrun_timeout=pendulum.duration(minutes=60),
    tags=['import_data'],
) as dag:
    PythonOperator(
        task_id='import_data_mbfiber',
        python_callable=importDataMobifiberTask,
        retries=1,
        retry_delay=pendulum.duration(minutes=60),
    )
