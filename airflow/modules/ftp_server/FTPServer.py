from ftplib import FTP, error_perm, Error, error_proto, error_temp, all_errors
import os, sys, time, shutil, socket, traceback
from datetime import datetime
import fnmatch

class FTPServer:
    def __init__(self, connectConfig):
        self.connectConfig = connectConfig
        self.ftp = FTP()
        self.status = False
        self.files = []

    def parseDate(self, date: datetime):
        return date.strftime('%Y%m%d')
    
    def connectFTP(self, max_retries: int = 3, retry_delay: int = 5) -> bool:
        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔌 [Attempt {attempt}/{max_retries}] Connecting to FTP server...", flush=True)
                if getattr(self.ftp, "sock", None):
                    try:
                        self.ftp.quit()
                    except all_errors as e:
                        print(f"⚠️ Warning when closing old FTP connection: {e}", flush=True)
                    finally:
                        try:
                            self.ftp.close()
                        except Exception:
                            pass

                self.ftp = FTP(timeout=15)
                try:
                    self.ftp.connect(
                        self.connectConfig["host"],
                        int(self.connectConfig.get("port", 21))

                    )
                except socket.gaierror as e:
                    print(f"❌ DNS resolution failed for host {self.connectConfig['host']}: {e}", flush=True)
                    return False
                except (socket.timeout, ConnectionRefusedError) as e:
                    print(f"❌ Cannot reach FTP server (timeout/refused): {e}", flush=True)
                    continue
                except OSError as e:
                    print(f"⚠️ OS-level socket error: {e}", flush=True)
                    traceback.print_exc()
                    continue
                try:
                    self.ftp.login(
                        self.connectConfig["username"],
                        self.connectConfig["password"]
                    )
                except error_perm as e:
                    print(f"🚫 Permission denied (wrong username/password): {e}", flush=True)
                    return False
                except error_temp as e:
                    print(f"⏳ Temporary FTP error during login: {e}", flush=True)
                    time.sleep(retry_delay)
                    continue
                except error_proto as e:
                    print(f"⚠️ Protocol error during FTP login: {e}", flush=True)
                    continue
                except Exception as e:
                    print(f"⚠️ Unexpected error during login: {e}", flush=True)
                    traceback.print_exc()
                    continue

                self.status = True
                print(f"✅ Connected to FTP server: {self.connectConfig['host']}", flush=True)
                return True

            except all_errors + (socket.error, socket.timeout) as e:
                self.status = False
                print(f"❌ Connection attempt {attempt} failed: {e}", flush=True)
                traceback.print_exc()
                if attempt < max_retries:
                    print(f"⏳ Retrying in {retry_delay} seconds...", flush=True)
                    time.sleep(retry_delay)
                else:
                    print("🚫 Max retries reached. Could not connect to FTP server.", flush=True)
                    return False

            except Exception as e:
                self.status = False
                print(f"⚠️ Unexpected fatal error: {e}", flush=True)
                traceback.print_exc()
                return False

            finally:
                sys.stdout.flush()

        return False



    def downloadFile(self, remoteDir, fname, localDir, chunk_size=8192):
        localPath = os.path.join(localDir, fname)
        os.makedirs(localDir, mode=0o755, exist_ok=True) 

        try:
            self.ftp.cwd(remoteDir)
            size = self.ftp.size(fname)
            downloaded = os.path.getsize(localPath) if os.path.exists(localPath) else 0
            mode = "ab" if downloaded < size and downloaded > 0 else "wb"
            if downloaded >= size:
                print(f"✅ Already downloaded: {fname}")
                return True
            if downloaded > 0:
                self.ftp.sendcmd(f"REST {downloaded}")
                print(f"🔁 Resume {fname} from {downloaded}")

            start = time.time()
            def callback(data):
                nonlocal downloaded
                with open(localPath, mode="ab") as f:
                    f.write(data)
                downloaded += len(data)
            self.ftp.retrbinary(f"RETR {fname}", callback, blocksize=chunk_size)

            elapsed = time.time() - start
            print(f"✅ Done: {fname} ({size/1024/1024:.2f} MB, {downloaded/1024/1024/elapsed:.2f} MB/s avg)")
            return True

        except error_perm as e:
            print(f"[WARN] File not found: {fname} ({e})")
            return False
        except Exception as e:
            print(f"[ERROR] Download error {fname}: {e}")
            if os.path.exists(localPath):
                os.remove(localPath)
            return False


    def uploadFile(self, localFilePath: str, remotePath: str):
        if not self.status:
            print("❌ FTP connection not established")
            return False
        if not os.path.isfile(localFilePath):
            print(f"⚠️ Local file not found: {localFilePath}")
            return False
        try:
            self.ftp.cwd(remotePath)
        except Exception:
            print(f"⚠️ Remote path not found, creating: {remotePath}")
            try:
                for part in remotePath.strip("/").split("/"):
                    try:
                        self.ftp.mkd(part)
                    except Exception:
                        pass
                    self.ftp.cwd(part)
            except Exception as e:
                print(f"❌ Could not create remote path: {e}")
                return False

        try:
            fileName = os.path.basename(localFilePath)
            with open(localFilePath, "rb") as f:
                self.ftp.storbinary(f"STOR {fileName}", f)
            print(f"✅ Uploaded: {localFilePath} → {remotePath}/{fileName}")
            return True
        except Exception as e:
            print(f"❌ FTP upload failed: {e}")
            return False

    def disconnectFTP(self):
        if self.status:
            try:
                self.ftp.quit()
                print("Disconnected from FTP successfully")
            except Exception as e:
                print(f"Error disconnecting from FTP: {e}")
        else:
            print("FTP is not connected")

