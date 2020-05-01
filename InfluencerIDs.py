import requests
from time import sleep
from csv import writer
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import yaml


chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9999")
chrome_driver = "C:\selenium\chromedriver.exe"
driver = webdriver.Chrome(options=chrome_options)
driver.implicitly_wait(10)
#self.driver = webdriver.Chrome()
driver.get('https://displate.com/admin/users/all')


with open ('influencers.yml', 'r') as stream:
    influencers = yaml.safe_load(stream)

def write():
    id = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td.sorting_1')
    nick = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td:nth-child(2)')
    firstName = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td:nth-child(3)')
    lastName = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td:nth-child(4)')
    email = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td:nth-child(5)')
    aaCode = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td:nth-child(6)') 

    with open('influencers.csv', 'w') as csv_file:
            csv_writer = writer(csv_file)
            headers = ['ID', 'Nickname', 'First Name', 'Last Name', 'Email', 'Art Agent Code']
            csv_writer.writerow(headers)
            csv_writer.writerow([id[0].text, nick[0].text, firstName[0].text, lastName[0].text, email[0].text, aaCode[0].text,])

def append():
    sleep(8)
    id = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td.sorting_1')
    nick = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td:nth-child(2)')
    firstName = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td:nth-child(3)')
    lastName = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td:nth-child(4)')
    email = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td:nth-child(5)')
    aaCode = driver.find_elements_by_css_selector('#DataTables_Table_0 > tbody > tr > td:nth-child(6)')
    
    with open('influencers.csv', 'a') as csv_file:
        csv_writer = writer(csv_file)
        csv_writer.writerow([id[0].text, nick[0].text, firstName[0].text, lastName[0].text, email[0].text, aaCode[0].text,])
    
account = 1
while account <= influencers['Accounts']:
    if account == 1:
        search = driver.find_element_by_xpath('//*[@id="DataTables_Table_0_filter"]/label/input')
        search.send_keys(influencers['user1'])
        write()
        
    if account == 2:
        search = driver.find_element_by_xpath('//*[@id="DataTables_Table_0_filter"]/label/input')
        search.clear()
        search.send_keys(influencers['user2'])
        append()
            
    if account == 3:
        search = driver.find_element_by_xpath('//*[@id="DataTables_Table_0_filter"]/label/input')
        search.clear()
        search.send_keys(influencers['user3'])
        append()
    if account == 4:
        search = driver.find_element_by_xpath('//*[@id="DataTables_Table_0_filter"]/label/input')
        search.clear()
        search.send_keys(influencers['user4'])
        append()
    if account == 5:
        search = driver.find_element_by_xpath('//*[@id="DataTables_Table_0_filter"]/label/input')
        search.clear()
        search.send_keys(influencers['user5'])
        append()
    if account == 6:
        search = driver.find_element_by_xpath('//*[@id="DataTables_Table_0_filter"]/label/input')
        search.clear()
        search.send_keys(influencers['user6'])
        append()
    if account == 7:
        search = driver.find_element_by_xpath('//*[@id="DataTables_Table_0_filter"]/label/input')
        search.clear()
        search.send_keys(influencers['user7'])
        append()
    if account == 8:
        search = driver.find_element_by_xpath('//*[@id="DataTables_Table_0_filter"]/label/input')
        search.clear()
        search.send_keys(influencers['user8'])
        append()
    if account == 9:
        search = driver.find_element_by_xpath('//*[@id="DataTables_Table_0_filter"]/label/input')
        search.clear()
        search.send_keys(influencers['user9'])
        append()
    if account == 10:
        search = driver.find_element_by_xpath('//*[@id="DataTables_Table_0_filter"]/label/input')
        search.clear()
        search.send_keys(influencers['user10'])
        append()
    if account == 11:
        search = driver.find_element_by_xpath('//*[@id="DataTables_Table_0_filter"]/label/input')
        search.clear()
        search.send_keys(influencers['user11'])
        append()

    account += 1    
    

    
