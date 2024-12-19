from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from dotenv import load_dotenv
from os.path import join, dirname
import os
import time
from common import *

dotenvPath = join(dirname(__file__), ".env")
load_dotenv(dotenvPath)
BIG_DATA_USERNAME = os.getenv("BIG_DATA_USERNAME")
BIG_DATA_PASSWORD = os.getenv("BIG_DATA_PASSWORD")
BIG_DATA_LINK = os.getenv("BIG_DATA_LINK")
BIG_DATA_LINK2 = os.getenv("BIG_DATA_LINK2")
FIREFOX_LINK = os.getenv("FIREFOX_LINK")

firefoxBinaryPath = "/usr/bin/firefox"
service = Service(executable_path="/usr/local/bin/geckodriver")

downloadPath = os.path.abspath("files")
options = Options()
options.binary_location = firefoxBinaryPath
options.add_argument("--headless") 
options.add_argument("--no-sandbox") 
options.add_argument("--disable-dev-shm-usage") 
options.add_argument("--disable-gpu") 
options.set_preference("browser.download.folderList", 2)  
options.set_preference("browser.download.dir", downloadPath)
options.set_preference("browser.helperApps.neverAsk.saveToDisk",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel")


driver = webdriver.Firefox(service=service, options=options)


try:
    driver.get(BIG_DATA_LINK)
    username = driver.find_element(By.ID, "form_login:username")
    password = driver.find_element(By.ID, "form_login:password")
    username.send_keys(BIG_DATA_USERNAME)
    password.send_keys(BIG_DATA_PASSWORD)
    password.send_keys(Keys.ENTER)
    
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "content-center"))
    )

    menuBaoCaoThueBao = driver.find_element(By.XPATH, "//a/span[text()='Báo cáo thuê bao']")
    menuBaoCaoThueBao.click()
    
    menuBaoCaoGoiCuoc = driver.find_element(By.XPATH, "//a/span[text()='Báo cáo tổng hợp gói cước']")
    menuBaoCaoGoiCuoc.click()
    
    startDateButton = WebDriverWait(driver, 60 * 5).until(
        EC.element_to_be_clickable((By.XPATH, "//span[@id='form_main:sta_date1']//button"))
    )
    startDateButton.click()
    
    day, month, year = getDate()
    startDayXpath = f"//td[@data-handler='selectDay' and @data-month='{month - 1}' and @data-year='{year}']/a[text()='{day - 1}']"
    try:
        date_to_select = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, startDayXpath))
        )
        date_to_select.click()

    except TimeoutException:
        print(f"Không tìm thấy ngày bắt đầu với XPath: {startDayXpath}")
        
    endDateButton = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, "//span[@id='form_main:end_date1']//button"))
    )
    endDateButton.click()
    
    endDayXpath = f"//td[@data-handler='selectDay' and @data-month='{month - 1}' and @data-year='{year}']/a[text()='{day - 1}']"
    try:
        date_to_select = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, endDayXpath))
        )
        date_to_select.click()

    except TimeoutException:
        print(f"Không tìm thấy ngày bắt đầu với XPath: {endDayXpath}")
        
    mucHienThi = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "form_main:muc_hien_thi_label"))
    )
    mucHienThi.click()
    
    driver.execute_script("document.getElementById('form_main:muc_hien_thi_input').value = '04';")

    downloadButton = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Xuất Excel']]"))
    )
    downloadButton.click()
    time.sleep(60 * 5)

finally:
    driver.quit()
