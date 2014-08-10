#!/usr/bin/env python

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import mechanize
import os
import pandas.io.sql as psql
import pymysql as mdb
import time
import re
import unicodedata

class artPriceBrowser(object):
    
    '''
        Here we login to ArtPrice.com with the user account from the homepage
        Sleeps are required for page to completely load
    '''
    
    def __init__(self, username, password):
        driver = webdriver.Chrome('/Users/daniel/Downloads/chromedriver')
        print 'finished the driver'
        driver.get("http://artprice.com/identity")
        print 'b4 sleep'
        time.sleep(1)
        print 'after sleep'
        elem = driver.find_element_by_id("login")
        elem.send_keys(username)
        elem = driver.find_element_by_id("pass")
        elem.send_keys(password)
        elem = driver.find_element_by_name("commit")
        elem.click()
        print 'supposedly logged in before sleep 2'
        time.sleep(2)
        print 'after sleep 2'
        self._driver = driver
        #html= driver.find_element_by_xpath(".//html")
        #print html; raw_input()
    
    def downloadHtml(self):
        elem = self._driver.find_element_by_xpath("//*")
        source_code = elem.get_attribute("outerHTML")
        return source_code
    
    def saveHtml(self, html_source, file_dir, file_name):
        full_name = os.path.join(file_dir,file_name+'.html') 
        f = open(full_name, 'w')
        f.write(html_source.encode('utf-8'))
        f.close()
        
    def getArtistPage(self, artist_link, page_number, scroll = 5):
        prefix_url = 'http://www.artprice.com/artist/'
        suffix_url = '/lots/pasts?iso3=USD&p=%s&sort=datesale_desc&unite_to=cm' %(page_number)
        tmp_url = '%s%s%s' %(prefix_url, artist_link, suffix_url)
        self._driver.get(tmp_url)
        time.sleep(2)
        for i in range(scroll):
            self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        return self.downloadHtml()
    
    def saveArtistPage(self, artist_link, page_number, file_name, file_dir = '/Users/daniel/insight/artprice_html_files/', scroll = 5):
        prefix_url = 'http://www.artprice.com/artist/'
        suffix_url = '/lots/pasts?iso3=USD&p=%s&sort=datesale_desc&unite_to=cm' %(page_number)
        tmp_url = '%s%s%s' %(prefix_url, artist_link, suffix_url)
        self._driver.get(tmp_url)
        time.sleep(1)
        for i in range(scroll):
            self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        html_source = self.downloadHtml()
        return self.saveHtml(html_source, file_dir, file_name)
    
    def logOut(self):
        elem = self._driver.find_element_by_id("logout_lnk")
        elem.click()
        

def readSqlSelectIntoPandasDf(sql_command):
    ''' Read a select statement into a panda dataframe '''
    mysql_cn= mdb.connect('localhost', 'root','','abstrart_db')
    df = psql.frame_query(sql_command, con=mysql_cn)
    mysql_cn.close()
    return df

# First, Login to artprice.com
# browser = loginToArtPrice()
username = 'dfernan@gmail.com'
password = 'ledc1182'
browser = artPriceBrowser(username, password)

# Second, Get the links for a given artist
artists = readSqlSelectIntoPandasDf('select link from pantheon')['link']

# Third, Scrape each field_name and field_value for a given auction
auction_id_regex = re.compile("(?:(?m)pasts/([0-9]{1,}))")
#painting_image_link_regex = re.compile("(?:(?m)\"(http://imgprivate2.artprice.com/lot/[A-Za-z0-9=/]{1,})\")")
prefix_url = 'http://www.artprice.com/artist/'
suffix_url = '/lots/pasts?iso3=USD&p=1&sort=datesale_desc&unite_to=cm'
npages_regex = re.compile("(?:(?m)amp;p=([0-9]{0,}))")
for artist_link in artists:
    artist_id = artist_link.split('/')[0]
    artist_name = artist_link.split('/')[1]
    print artist_name
    artist_html = browser.getArtistPage(artist_link, 1)
    npages_match = npages_regex.findall(artist_html)
    npages_match = max([int(page) for page in npages_match])
    print 'Downloading each page for artist %s from %s pages' %(artist_name, npages_match)
    auction_count = 0
    for page_number in range(1, npages_match+1):
        print 'downloading for artist %s page %s' %(artist_name, page_number)
        suffix_url = '/lots/pasts?iso3=USD&p=%s&sort=datesale_desc&unite_to=cm' %(page_number)
        browser.saveArtistPage(artist_link, page_number, artist_name.replace('-','')+'_p'+str(page_number))                 
browser.logOut()