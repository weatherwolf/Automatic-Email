from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import pandas as pd
import numpy as np
import time
from selenium.webdriver.chrome.options import Options
import openpyxl

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager



def VATNumberValid(VATNumber, countryList, driver):
    selectCountry = "none"
    for country in countryList:
        if country in VATNumber:
            selectCountry = country
            split = VATNumber.split(country, 1)
            VATNumber = str(split[1])
            break
    if selectCountry == "none": #If selectCountry == "none", break of program and tell VAT number doens' exist
        return f"DO BY HAND"

    #Going to website
    driver.get('https://ec.europa.eu/taxation_customs/vies/#/vat-validation')


    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="select-country"]')))
        #Fill in the country of the recipient
        time.sleep(1)
        select_country = Select(driver.find_element(By.XPATH, '//*[@id="select-country"]'))
        select_country.select_by_value(selectCountry)
    except: 
        return "DO BY HAND"


    #fill in BTW of recipient
    select_VAT_Number = driver.find_element(By.XPATH, '//*[@id="vat-validation-form"]/div/div[2]/input')
    select_VAT_Number.send_keys(VATNumber)
    select_VAT_Number.send_keys(Keys.RETURN)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'valid'))
            )
        return "YES"
    except:
        pass
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'FAQ'))
            )
        return "INCORRECT BTW"
    except:
       pass
    try:
        WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'invalid'))
            )
        return "DATABASE DOWN"
    except:
        pass
    try:
        WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'FAQ'))
            )
        return "INCORRECT BTW"
    except:
        return "SITE NOT LOADING"


def MakeDatabase(vat_numbers_df, countryList, driver):
    btwNummers = []
    outputs = []
    database_down_country = "none"

    # Assuming vat_numbers_df is a pandas DataFrame with one column
    # Extract the VAT numbers from that column
    vat_numbers_series = vat_numbers_df.iloc[:, 0].dropna()

    for vatNumber in vat_numbers_series:
        vatNumber = str(vatNumber).strip()
        print(vatNumber)
        if database_down_country in vatNumber:
            btwNummers.append(vatNumber)
            outputs.append("DATABASE DOWN")
        else:
            output = VATNumberValid(vatNumber, countryList, driver)
            while output == "DO BY HAND":
                output = VATNumberValid(vatNumber, countryList, driver)
            btwNummers.append(vatNumber)
            outputs.append(output)
            if output == "DATABASE DOWN":
                for country in countryList:
                    if country in vatNumber:
                        database_down_country = country
                        break  # Exit loop after finding the country
    return pd.DataFrame(data={"Vat Number": btwNummers, "Output": outputs})


def run_vat_checker(inputfile):
    countryList = np.array(["AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR", "HU", "IE", "IT", "LU", "LT", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "XI"])

    options = Options()
    options.headless = True  # Change to False if you want to see the browser
    options.add_argument("--headless")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    df = MakeDatabase(inputfile, countryList, driver)

    return df
    