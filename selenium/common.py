import pandas as pd
from datetime import datetime
import glob
import os 
def deleteNNumberRow(fileName, n):
    filePath = fileName
    df = pd.read_excel(filePath)
    df = df.iloc[n:]
    df.to_excel(fileName, index=False, header=False)

def getDate():
    currentDate = datetime.now()
    day = currentDate.day
    month = currentDate.month
    year = currentDate.year
    return day, month, year

def getExcelDirectory(folderPath):
    excelFiles = glob.glob(os.path.join(folderPath, "*.xlsx")) + glob.glob(os.path.join(folderPath, "*.xls"))
    latestFile = max(excelFiles, key=os.path.getmtime)
    return latestFile

def readFileExcel(fileName):
    data = pd.read_excel(fileName, header=None)
    data = data.where(pd.notnull(data), '')
    return data
