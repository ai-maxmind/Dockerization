import os

class Utils:
    @staticmethod
    def deleteFile(localFilePath: str):
        if os.path.exists(localFilePath):
            os.remove(localFilePath)
            print(f"✅ Deleted file: {localFilePath}")
        else:
            print(f"⚠️ File not found: {localFilePath}")

    @staticmethod
    def findConfigFile(fileName="env.ini") -> str:
        d = os.path.abspath(os.path.dirname(__file__))
        while d != os.path.dirname(d):
            f = os.path.join(d, fileName)
            if os.path.isfile(f):
                return f
            d = os.path.dirname(d)
        raise FileNotFoundError(f"❌ {fileName} not found in parent directories")
    
    @staticmethod
    def getCheckpointFileName(taskId: str, filePath: str) -> str:
        baseName = os.path.basename(filePath)
        if baseName.endswith(".gz"):
            baseName = os.path.splitext(os.path.splitext(baseName)[0])[0]
        else:
            baseName = os.path.splitext(baseName)[0]

        return f"checkpoint_{taskId}_{baseName}.json"

