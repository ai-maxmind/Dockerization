import oracledb
from typing import Optional, List, Dict, Any, Tuple
import re, time, logging, traceback, json, os
import pandas as pd

class OracleDB:
    def __init__(self, connectConfig, maxRetries: int = 3, retryDelay: int = 3):
        self.connectConfig = connectConfig
        self.pool: Optional[oracledb.ConnectionPool] = None
        self.conn: Optional[oracledb.Connection] = None
        self.maxRetries = maxRetries
        self.retryDelay = retryDelay

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.closeDB()

    def connectDB(self) -> bool:
        attempt = 0
        delay = getattr(self, "retryDelay", 2)  
        maxDelay = getattr(self, "maxRetryDelay", 60)  

        while attempt < getattr(self, "maxRetries", 5):
            try:
                logging.info(f"🔗 Creating Oracle connection pool... (attempt {attempt+1})")

                self.pool = oracledb.create_pool(
                    user=self.connectConfig["username"],
                    password=self.connectConfig["password"],
                    host=self.connectConfig["host"],
                    port=self.connectConfig["port"],
                    service_name=self.connectConfig["service_name"],
                    min=2,
                    max=20,
                    increment=2,
                    timeout=120,
                    getmode=oracledb.POOL_GETMODE_WAIT,
                    ping_interval=60,
                    homogeneous=True,
                    session_callback=getattr(self, "sessionInit", None)
                )

                self.conn = self.pool.acquire()
                self.conn.autocommit = False
                self.verifyConnection()
                self.checkpointFile = "checkpoint.json"
                logging.info("✅ Oracle connection pool created and connection acquired.")
                return True

            except oracledb.DatabaseError as e:
                err = e.args[0]
                logging.error(f"❌ DatabaseError {err.code}: {err.message.strip()}")
                logging.error(traceback.format_exc())
                attempt += 1
                if attempt < getattr(self, "maxRetries", 5):
                    logging.warning(f"🔁 Retrying in {delay}s (exponential backoff)...")
                    time.sleep(delay)
                    delay = min(delay * 2, maxDelay) 
                else:
                    logging.error("❌ Max retries reached, cannot connect to Oracle DB.")
                    return False

            except Exception as e:
                logging.error(f"❌ Unexpected error: {e}")
                logging.error(traceback.format_exc())
                return False

        return False

    def saveCheckpoint(self, offset: int):
        with open(self.checkpointFile, "w") as f:
            json.dump({"last_index": offset}, f)

    def loadCheckpoint(self) -> int:
        if os.path.exists(self.checkpointFile):
            with open(self.checkpointFile, "r") as f:
                data = json.load(f)
                return data.get("last_index", 0)
        return 0

    def clearCheckpoint(self):
        if os.path.exists(self.checkpointFile):
            os.remove(self.checkpointFile)


    def getConnection(self) -> Optional[oracledb.Connection]:
        try:
            if not self.pool:
                logging.warning("⚠️ Pool chưa được khởi tạo, đang tạo lại...")
                if not self.connectDB():
                    raise Exception("Không thể khởi tạo pool.")

            conn = self.pool.acquire()
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM DUAL")
            logging.debug("✅ Connection acquired successfully from pool.")
            return conn

        except Exception as e:
            logging.warning(f"⚠️ Connection invalid or expired: {e}")
            self.resetPool()
            return self.pool.acquire()


    def rollbackConnection(self):
        if hasattr(self, "conn") and self.conn:
            try:
                self.conn.rollback()
                logging.info("↩️ Transaction rolled back successfully.")
            except Exception as e:
                logging.warning(f"⚠️ Rollback failed: {e}")

    def resetPool(self):
        if self.pool:
            try:
                logging.warning("🔁 Resetting Oracle connection pool...")
                self.pool.close(force=True)
                time.sleep(2)
                self.connectDB()
            except Exception as e:
                logging.error(f"⚠️ Pool reset failed: {e}")


    def sessionInit(self, conn, requestedTag):
        try:
            with conn.cursor() as cur:
                session_cmds = [
                    "ALTER SESSION ENABLE PARALLEL DML",
                    "ALTER SESSION SET parallel_force_local = TRUE",
                    "ALTER SESSION SET commit_logging = BATCH",
                    "ALTER SESSION SET commit_wait = NOWAIT",
                    "ALTER SESSION SET cursor_sharing = FORCE",
                    "ALTER SESSION SET optimizer_mode = FIRST_ROWS_1000",
                    "ALTER SESSION SET optimizer_dynamic_sampling = 4",
                    "ALTER SESSION SET optimizer_index_cost_adj = 50",
                    "ALTER SESSION SET result_cache_mode = FORCE",
                    "ALTER SESSION SET nls_date_format = 'YYYY-MM-DD HH24:MI:SS'",
                    "ALTER SESSION SET nls_timestamp_format = 'YYYY-MM-DD HH24:MI:SS.FF'",
                    "ALTER SESSION SET nls_numeric_characters = '.,'",
                    "ALTER SESSION SET workarea_size_policy = AUTO",
                    "ALTER SESSION SET hash_area_size = 16777216",
                    "ALTER SESSION SET sort_area_size = 16777216",
                    "ALTER SESSION SET session_cached_cursors = 2000"
                ]
                for cmd in session_cmds:
                    cur.execute(cmd)
            logging.info("✅ Oracle session initialized and optimized.")
        except Exception as e:
            logging.warning(f"⚠️ Session init failed: {e}")


    def verifyConnection(self):
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 'CONNECTED' FROM DUAL")
                logging.info(f"✅ Verified: {cur.fetchone()[0]}")
        except Exception as e:
            logging.warning(f"⚠️ Connection verification failed: {e}")

    def reconnect(self, maxRetries: int = 3, retryDelay: int = 5):
        logging.info("🔄 Attempting to reconnect to Oracle database...")
        try:
            if self.conn:
                try:
                    self.conn.close()
                    logging.info("🔒 Old connection closed.")
                except Exception as e:
                    logging.warning(f"⚠️ Failed to close old connection: {e}")
                finally:
                    self.conn = None
        except Exception as e:
            logging.warning(f"⚠️ Error cleaning old connection: {e}")

        for attempt in range(1, maxRetries + 1):
            try:
                if hasattr(self, 'pool') and self.pool:
                    self.conn = self.pool.acquire()
                    logging.info(f"✅ Reconnected via connection pool (attempt {attempt}).")
                else:
                    self.conn = oracledb.connect(
                        user=self.user,
                        password=self.password,
                        dsn=self.dsn
                    )
                    logging.info(f"✅ Reconnected directly (attempt {attempt}).")
                    
                if self.conn.is_healthy():
                    logging.info("🩺 Connection is healthy after reconnection.")
                    return True
                else:
                    logging.warning("⚠️ Connection appears unhealthy after reconnection.")

            except Exception as e:
                logging.warning(f"❌ Reconnection attempt {attempt} failed: {type(e).__name__} - {e}")

            if attempt < maxRetries:
                logging.info(f"⏳ Retrying in {retryDelay} seconds...")
                time.sleep(retryDelay)

        logging.error("🚨 All reconnection attempts failed.")
        return False

    def disableTriggersConstraints(self, tableName: str):
        with self.conn.cursor() as cur:
            cur.execute(f"""
                BEGIN
                    FOR t IN (SELECT trigger_name FROM user_triggers WHERE table_name = UPPER('{tableName}'))
                    LOOP
                        EXECUTE IMMEDIATE 'ALTER TRIGGER ' || t.trigger_name || ' DISABLE';
                    END LOOP;
                END;
            """)
            cur.execute(f"""
                BEGIN
                    FOR c IN (SELECT constraint_name, constraint_type
                              FROM user_constraints
                              WHERE table_name = UPPER('{tableName}') 
                                AND constraint_type IN ('R','C'))  -- R=FK, C=CHECK
                    LOOP
                        EXECUTE IMMEDIATE 'ALTER TABLE {tableName} DISABLE CONSTRAINT ' || c.constraint_name;
                    END LOOP;
                END;
            """)
            
    def enableTriggersConstraints(self, tableName: str):
        with self.conn.cursor() as cur:
            cur.execute(f"""
                BEGIN
                    FOR t IN (SELECT trigger_name FROM user_triggers WHERE table_name = UPPER('{tableName}'))
                    LOOP
                        EXECUTE IMMEDIATE 'ALTER TRIGGER ' || t.trigger_name || ' ENABLE';
                    END LOOP;
                END;
            """)
            cur.execute(f"""
                BEGIN
                    FOR c IN (SELECT constraint_name, constraint_type
                              FROM user_constraints
                              WHERE table_name = UPPER('{tableName}') 
                                AND constraint_type IN ('R','C'))
                    LOOP
                        EXECUTE IMMEDIATE 'ALTER TABLE {tableName} ENABLE CONSTRAINT ' || c.constraint_name;
                    END LOOP;
                END;
            """)
    def setNologging(self, tableName: str):
        with self.conn.cursor() as cur:
            cur.execute(f"ALTER TABLE {tableName} NOLOGGING")

    def validateIdentifier(self, name: str) -> bool:
        return bool(re.match(r"^[A-Z0-9_]+(\.[A-Z0-9_]+)*$", name, re.IGNORECASE))

    def safeCondition(self, condition: str) -> bool:
        if not condition or condition.strip() == "":
            print("🚫 Unsafe operation: WHERE condition required.")
            return False
        return True

    def executeSQL(self,sql: str,params: Optional[List[Any]] = None,
                    many: bool = False,returnResult: bool = False,
                    commit_each_batch: bool = True, batch_size: int = 1000000,retries: int = 3):
    
        attempt = 0
        while attempt < retries:
            conn = None
            try:
                conn = self.getConnection()
                if not conn:
                    print("❌ Could not acquire connection from pool.")
                    return None if returnResult else False

                with conn.cursor() as cur:
                    if many:
                        total = len(params or [])
                        for i in range(0, total, batch_size):
                            batch = params[i:i + batch_size]
                            cur.executemany(sql, batch)
                            if commit_each_batch:
                                conn.commit()
                    else:
                        cur.execute(sql, params or [])
                        if returnResult:
                            columns = [col[0] for col in cur.description]
                            rows = cur.fetchall()
                            return pd.DataFrame(rows, columns=columns)

                    if not commit_each_batch:
                        conn.commit()

                return True

            except Exception as e:
                attempt += 1
                print(f"⚠️ Attempt {attempt}/{retries} failed: {type(e).__name__} - {str(e)}")

                try:
                    if conn:
                        conn.rollback()
                except Exception:
                    pass

                print("🔁 Reconnecting to Oracle...")
                self.connectDB()
                time.sleep(3)

                if attempt >= retries:
                    print(f"❌ SQL Execution failed after {retries} attempts: {e}")
                    return None if returnResult else False

         

    def selectData(self, tableName: str, cols: List[str], whereClause: Optional[str] = None,
                        params: Optional[List[Any]] = None,retries: int = 3) -> List[Dict[str, Any]]:
        sql = f"SELECT {', '.join(cols)} FROM {tableName}"
        if whereClause:
            sql += f" WHERE {whereClause}"

        attempt = 0
        while attempt < retries:
            conn = None
            try:
                conn = self.getConnection()
                if not conn:
                    print("❌ Could not acquire connection from pool.")
                    return []

                with conn.cursor() as cursor:
                    cursor.execute(sql, params or [])
                    colnames = [d[0] for d in cursor.description]
                    results = [dict(zip(colnames, row)) for row in cursor.fetchall()]
                    return results

            except Exception as e:
                attempt += 1
                print(f"⚠️ Attempt {attempt}/{retries} failed: {type(e).__name__} - {e}")

                try:
                    if conn:
                        conn.rollback()
                except Exception:
                    pass

                print("🔁 Reconnecting to Oracle...")
                self.connectDB()
                time.sleep(3)

                if attempt >= retries:
                    print(f"❌ Query failed after {retries} retries: {e}")
                    return []


    def deleteData(self, tableName: str, condition: str):
        if not (self.validateIdentifier(tableName) and self.safeCondition(condition)):
            return False
        sql = f"DELETE FROM {tableName} WHERE {condition}"
        return self.executeSQL(sql)
    def truncateTable(self, tableName: str):
        if not self.validateIdentifier(tableName):
            return False
        sql = f"TRUNCATE TABLE {tableName}"
        return self.executeSQL(sql)


    
    def insertData(self, tableName: str, cols: List[str], data: List[Dict[str, Any]],
               batchSize: int = 1000000, retries: int = 3) -> bool:

        if not data:
            logging.warning("⚠️ No data to insert.")
            return False

        sql = (
            f"INSERT INTO {tableName} ({','.join(cols)}) "
            f"VALUES ({','.join([f':{i+1}' for i in range(len(cols))])})"
        )

        startIndex = self.loadCheckpoint()
        totalData = len(data)
        logging.info(f"🚀 Start inserting {totalData} rows from row {startIndex}")

        attempt = 0
        while attempt < retries:
            conn = None
            try:
                conn = self.pool.acquire()
                conn.autocommit = False
                conn.call_timeout = 0

                with conn.cursor() as cur:
                    cur.arraysize = batchSize
                    cur.prefetchrows = batchSize

                    values = [[row.get(c) for c in cols] for row in data[0:]]
                    totalInserted = 0

                    for i in range(0, len(values), batchSize):
                        batch = values[i:i + batchSize]
                        currentIndex = startIndex + i

                        cur.executemany(sql, batch, batcherrors=True, arraydmlrowcounts=True)
                        conn.commit()

                        self.saveCheckpoint(currentIndex + len(batch))
                        totalInserted += len(batch)
                        logging.info(f"✅ Inserted rows {currentIndex + 1:,} → {currentIndex + len(batch):,} "
                                    f"(batch {len(batch):,}, total inserted {totalInserted:,})")

                self.clearCheckpoint() 
                return True

            except oracledb.DatabaseError as e:
                err = e.args[0]
                logging.error(f"⚠️ Oracle error {err.code}: {err.message.strip()}")
                if conn:
                    conn.rollback()
                attempt += 1
                logging.warning(f"🔁 Retry {attempt}/{retries} after 3s...")
                time.sleep(3)

            except Exception as e:
                logging.error(f"❌ Unexpected error: {type(e).__name__} - {e}")
                logging.error(traceback.format_exc())
                if conn:
                    conn.rollback()
                attempt += 1
                time.sleep(3)

            finally:
                if conn:
                    self.pool.release(conn)

        logging.error(f"💥 Insert failed after {retries} attempts.")
        return False
    
    # def insertData(self, tableName: str, cols: List[str], data: List[Dict[str, Any]],
    #            batchSize: int = 1000000, retries: int = 3) -> bool:
    #     if not data or not self.validateIdentifier(tableName):
    #         logging.warning("⚠️ Không có dữ liệu hoặc tên bảng không hợp lệ.")
    #         return False
    #     if not all(self.validateIdentifier(c) for c in cols):
    #         logging.warning("⚠️ Tên cột không hợp lệ.")
    #         return False

    #     sql = (
    #          f"INSERT /*+ APPEND_VALUES NOLOGGING OPT_PARAM('_optimizer_use_feedback' 'false') */ "
    #          f"INTO {tableName} ({','.join(cols)}) "
    #          f"VALUES ({','.join([f':{i+1}' for i in range(len(cols))])})"
    #     )

    #     total_rows = len(data)
    #     start_idx = 0
    #     attempt = 0

    #     while attempt < retries:
    #         conn = None
    #         try:
    #             conn = self.getConnection()
    #             if not conn:
    #                 logging.error("❌ Không thể lấy connection từ pool.")
    #                 return False

    #             conn.autocommit = False
    #             conn.call_timeout = 0
    #             conn.stmtcachesize = 50

    #             with conn.cursor() as cur:
    #                 cur.arraysize = batchSize
    #                 cur.prefetchrows = batchSize

    #                 while start_idx < total_rows:
    #                     end_idx = min(start_idx + batchSize, total_rows)
    #                     batch = data[start_idx:end_idx]

    #                     # ✅ chuyển sang list chứ không dùng generator
    #                     batch_values = [[row.get(c) for c in cols] for row in batch]

    #                     try:
    #                         cur.executemany(sql, batch_values)
    #                         conn.commit()
    #                         start_idx = end_idx
    #                         logging.info(f"✅ Đã insert {end_idx}/{total_rows} dòng.")
    #                     except oracledb.DatabaseError as e:
    #                         err = e.args[0]
    #                         logging.error(f"⚠️ Oracle error tại batch {start_idx}-{end_idx}: {err.message.strip()}")
    #                         conn.rollback()
    #                         raise

    #             return True

    #         except Exception as e:
    #             logging.error(f"💥 Lỗi khi insert: {e}")
    #             logging.error(traceback.format_exc())
    #             attempt += 1
    #             if conn:
    #                 try:
    #                     conn.rollback()
    #                 except Exception:
    #                     pass
    #             self.connectDB()
    #             logging.warning(f"🔁 Thử lại lần {attempt}/{retries} sau 3s...")
    #             time.sleep(3)

    #     logging.error(f"❌ Insert thất bại sau {retries} lần thử.")
    #     return False

    
    def insertIgnoreDuplicate(self, tableName: str, cols: List[str], data: List[Dict[str, Any]], indexName: Optional[str] = None,
                                    batchSize: int = 50000, retries: int = 3) -> bool:
        if not data or not self.validateIdentifier(tableName):
            logging.warning("⚠️ No data or invalid table name")
            return False
        if not all(self.validateIdentifier(c) for c in cols):
            logging.warning("⚠️ Invalid column name detected")
            return False

        indexHint = (
            f"(+ IGNORE_ROW_ON_DUPKEY_INDEX({tableName} {indexName}))"
            if indexName else "(+ IGNORE_ROW_ON_DUPKEY_INDEX)"
        )
        sql = (
            f"INSERT /*+ {indexHint} APPEND PARALLEL({tableName},4) NOLOGGING */ "
            f"INTO {tableName} ({','.join(cols)}) "
            f"VALUES ({','.join([f':{i+1}' for i in range(len(cols))])})"
        )
        values = [[row.get(c) for c in cols] for row in data]

        attempt = 0
        while attempt < retries:
            conn = None
            try:
                conn = self.getConnection()
                if not conn:
                    logging.error("❌ Could not acquire connection from pool.")
                    return False

                conn.autocommit = False
                conn.call_timeout = 0
                conn.stmtcachesize = 100

                with conn.cursor() as cur:
                    cur.arraysize = batchSize
                    cur.prefetchrows = batchSize
                    cur.setinputsizes(None)

                    total_rows = len(values)
                    for i in range(0, total_rows, batchSize):
                        batch = values[i:i + batchSize]
                        cur.executemany(sql, batch, batcherrors=True, arraydmlrowcounts=True)
                        conn.commit()

                return True

            except oracledb.DatabaseError as e:
                err = e.args[0]
                logging.error(f"⚠️ Oracle Error {err.code}: {err.message.strip()}")
                try:
                    if conn:
                        conn.rollback()
                except Exception:
                    pass
                attempt += 1
                logging.warning(f"🔁 Retrying insert-ignore... (attempt {attempt}/{retries})")
                self.connectDB()
                time.sleep(3)

            except Exception as e:
                logging.error(f"❌ Unexpected error: {type(e).__name__} - {e}")
                logging.error(traceback.format_exc())
                try:
                    if conn:
                        conn.rollback()
                except Exception:
                    pass
                attempt += 1
                logging.warning(f"🔁 Retrying insert-ignore... (attempt {attempt}/{retries})")
                self.connectDB()
                time.sleep(3)

        

        logging.error(f"💥 Insert-ignore failed after {retries} attempts.")
        return False

    def updateData(self, tableName: str, data: Dict[str, Any], condition: Optional[str] = None) -> bool:
        if not data or not self.validateIdentifier(tableName):
            print("⚠️ Invalid data or table name")
            return False
        if not all(self.validateIdentifier(c) for c in data.keys()):
            print("⚠️ Invalid column name detected")
            return False
        if condition and not self.safeCondition(condition):
            print("⚠️ Unsafe condition detected")
            return False
        if not condition:
            print("⚠️ Missing WHERE condition — update skipped to prevent full-table update")
            return False

        setClause = ', '.join([f"{col} = :{i+1}" for i, col in enumerate(data.keys())])
        sql = f"UPDATE {tableName} SET {setClause} WHERE {condition}"
        params = list(data.values())

        return self.executeSQL(sql, params)
    
    def indexExists(self, indexName: str) -> bool:
        if not self.validateIdentifier(indexName):
            return False
        sql = "SELECT COUNT(*) AS CNT FROM USER_INDEXES WHERE INDEX_NAME = :1"
        df = self.executeSQL(sql, [indexName.upper()], returnResult=True)
        return df.iloc[0, 0] > 0 if df is not None else False

    def createIndex(self, indexName: str, tableName: str, columns: List[str], unique: bool = False) -> bool:

        if self.indexExists(indexName):
            print(f"⚠️ Index {indexName} already exists, skipping creation")
            return True 

        if not (self.validateIdentifier(indexName) and self.validateIdentifier(tableName)):
            print("⚠️ Invalid index or table name")
            return False
        if not all(self.validateIdentifier(col) for col in columns):
            print("⚠️ Invalid column name detected")
            return False

        uniqueStr = "UNIQUE" if unique else ""
        colsStr = ", ".join(columns)
        sql = f"CREATE {uniqueStr} INDEX {indexName} ON {tableName} ({colsStr})"
        return self.executeSQL(sql)

    def dropIndex(self, indexName: str) -> bool:
        if not self.indexExists(indexName):
            print(f"⚠️ Index {indexName} does not exist, skipping drop")
            return True  
        sql = f"DROP INDEX {indexName}"
        return self.executeSQL(sql)


    def prepareParams(self, cur, paramDefinition: List[Tuple[str, str, Any]]):
        bindVariable = []
        outIndices = {}

        for i, (name, ptype, value) in enumerate(paramDefinition):
            if ptype == "IN":
                bindVariable.append(value)
            elif ptype == "OUT":
                var = cur.var(oracledb.STRING)
                bindVariable.append(var)
                outIndices[name] = i
            elif ptype == "INOUT":
                var = cur.var(oracledb.STRING)
                var.setvalue(0, value)
                bindVariable.append(var)
                outIndices[name] = i

        return bindVariable, outIndices

    def runProcedure(self, procName: str, paramDefinition: Optional[List[Tuple[str, str, Any]]] = None) -> Dict[str, Any]:
        try:
            if not self.conn or not self.conn.is_healthy():
                print("⚠️ Connection is invalid or lost. Reconnecting...")
                self.reconnect() 

            if not self.validateIdentifier(procName):
                print("⚠️ Invalid procedure name")
                return {}

            with self.conn.cursor() as cur:
                if not paramDefinition:
                    cur.callproc(procName)
                    print(f"✅ Procedure {procName} executed successfully (no params)")
                    return {}

                bindVariable, out_idx = self.prepareParams(cur, paramDefinition)
                cur.callproc(procName, bindVariable)

                result = {name: bindVariable[idx].getvalue() for name, idx in out_idx.items()}
                print(f"✅ Procedure {procName} executed successfully")
                return result

        except oracledb.InterfaceError as e:
            print("⚠️ Connection lost during procedure execution:", str(e))
            try:
                self.reconnect()
                return self.runProcedure(procName, paramDefinition) 
            except Exception as retry_err:
                print("❌ Reconnection failed:", retry_err)
                return {}

        except Exception as e:
            print("❌ Procedure execution failed:", type(e).__name__, str(e))
            return {}

    def runProcedureWithCursor(self, procName: str, params: Optional[List[Any]] = None) -> Optional[List[Dict[str, Any]]]:
        if not self.conn:
            print("❌ No active connection")
            return None

        try:
            with self.conn.cursor() as cur:
                refCursor = self.conn.cursor()
                execParams = (params or []) + [refCursor] 
                cur.callproc(procName, execParams)

                columns = [desc[0] for desc in refCursor.description]
                rows = [dict(zip(columns, row)) for row in refCursor.fetchall()]
                return rows
        except Exception as e:
            print(f"❌ Procedure execution failed [{procName}]:", e)
            return None



    def runPackage(self, packageName: str, procName: str, paramDefinition: Optional[List[Tuple[str, str, Any]]] = None) -> Dict[str, Any]:
        fullName = f"{packageName}.{procName}"
        if not (self.validateIdentifier(packageName) and self.validateIdentifier(procName)):
            print("⚠️ Invalid package or procedure name")
            return {}

        try:
            with self.conn.cursor() as cur:
                if paramDefinition:
                    bindVariable, out_idx = self.prepareParams(cur, paramDefinition)
                    cur.callproc(fullName, bindVariable)
                    result = {name: bindVariable[idx].getvalue() for name, idx in out_idx.items()}
                else:
                    cur.callproc(fullName)
                    result = {}

                print(f"✅ Package {fullName} executed successfully")
                return result
        except Exception as e:
            print("❌ Package execution failed:", type(e).__name__, str(e))
            return {}


    def closeDB(self, maxRetries=5, baseDelay=1.0):
        try:
            conn = getattr(self, "conn", None)
            pool = getattr(self, "pool", None)

            if conn:
                try:
                    if hasattr(conn, "is_healthy") and conn.is_healthy():
                        pool.release(conn)
                        logging.info("🔒 Connection released to pool.")
                    else:
                        logging.warning("⚠️ Connection invalid or disconnected.")
                except Exception as e:
                    logging.warning(f"⚠️ Could not release connection: {e}")
                finally:
                    self.conn = None

            if pool:
                for attempt in range(1, maxRetries + 1):
                    try:
                        pool.close()
                        logging.info("🛑 Connection pool closed.")
                        self.pool = None
                        break
                    except Exception as e:
                        delay = baseDelay * attempt  
                        logging.warning(f"⚠️ Attempt {attempt} to close pool failed: {e}")
                        if attempt < maxRetries:
                            logging.info(f"⏳ Retrying to close pool in {delay:.1f}s...")
                            time.sleep(delay)
                        else:
                            logging.error("🚨 Cannot close pool after multiple attempts.")
                            self.pool = None

        except Exception as e:
            logging.warning(f"⚠️ Unexpected error during closeDB: {type(e).__name__} - {e}")
            self.conn = None
            self.pool = None





