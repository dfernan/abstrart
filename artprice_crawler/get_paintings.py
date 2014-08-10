#!/usr/bin/env python

import cookielib
import math
import mechanize
import pymysql as mdb
import pandas.io.sql as psql
import pickle
import re
import requests
import string
import sys
import urllib2
import urllib

def readSqlSelectIntoPandasDf(sql_command):
    ''' Read a select statement into a panda dataframe '''
    mysql_cn= mdb.connect('localhost', 'root','','abstrart_db')
    df = psql.frame_query(sql_command, con=mysql_cn)
    mysql_cn.close()
    return df

def loginToArtPrice():
    browser = mechanize.Browser()
    artprice_url = 'http://www.artprice.com/identity'
    browser.open(artprice_url)
    browser.select_form(nr = 0)
    browser.form['login'] = 'dfernan@gmail.com'
    browser.form['pass'] = 'ledc1182'
    browser.submit()
    return browser

browser = loginToArtPrice()
artists_dict = {}
#artists = pickle.load(open('/Users/daniel/insight/artprice_data/artists_links_%s_%s.p' %(start, end), 'rb'))
artists = readSqlSelectIntoPandasDf('select link from pantheon')['link']
#artists = artists[0:10]
prefix_url = 'http://www.artprice.com/artist/'
suffix_url = '/lots/pasts?iso3=USD&p=1&sort=datesale_desc&unite_to=cm'
npages_regex = re.compile("(?:(?m)amp;p=([0-9]{0,}))")
born_died_regex = re.compile("(?:(?m)auction\\ results\\ for\\ {0,}[A-Za-z\\ ]{0,}\\(([0-9c./\\-]{0,})\\))")
painting_link_regex = re.compile("(?:(?m)href=\"(.{0,}.)\"\\>Full\\ details\\</a\\>)")
csv_fh = open('/Users/daniel/insight/artprice_data/paintings_links.csv','w')
for artist_link in artists:
    artist_id = artist_link.split('/')[0]
    artist_name = artist_link.split('/')[1]
    print artist_name
    tmp_url = '%s%s%s' %(prefix_url, artist_link, suffix_url)
    print tmp_url
    try:
        artist_page = browser.open(tmp_url).read()
        npages_match = npages_regex.findall(artist_page)
        npages_match = max([int(page) for page in npages_match])
        print 'getting the links for %s from %s pages' %(artist_name, npages_match)
        born_died_match = born_died_regex.findall(artist_page)[0]
        if npages_match == 1:
            painting_link_match = painting_link_regex.findall(artist_page)
            artists_dict[artist_id] = painting_link_match
            csv_fh.write('%s,%s\n' %(artist_id, painting_link_match))
        elif npages_match > 1:
            for page_number in range(1, npages_match+1):
                print 'downloading links for artist %s page %s' %(artist_name, page_number)
                suffix_url = '/lots/pasts?iso3=USD&p=%s&sort=datesale_desc&unite_to=cm' %(page_number)
                tmp_url = '%s%s%s' %(prefix_url, artist_link, suffix_url)
                artist_page = browser.open(tmp_url).read()
                painting_link_match = painting_link_regex.findall(artist_page)
                if artist_id in artists_dict:
                    artists_dict[artist_id].extend(painting_link_match)
                    csv_fh.write('%s,%s\n' %(artist_id, painting_link_match))
                else:
                    artists_dict[artist_id] = painting_link_match
                    csv_fh.write('%s,%s\n' %(artist_id, painting_link_match))
            suffix_url = '/lots/pasts?iso3=USD&p=%s&sort=datesale_desc&unite_to=cm' %('1')
        else:
            print 'odd sthg odd!'
    except:
        print 'artist %s have something odd' %(artist_name)
        artists_dict[artist_id] = 'NULL'
        csv_fh.write('%s,%s\n' %(artist_id, 'NULL'))
csv_fh.close()
pickle.dump(artists_dict, open('/Users/daniel/insight/artprice_data/paintings_links.p','w'))
# [artist_id for (artist_id, value) in artists_dict.items() if value=='NULL']
