#!/usr/bin/env python

from bs4 import BeautifulSoup
import os
import pandas.io.sql as psql
import pymysql as mdb
import re
import unicodedata

def removeAccents(input_str):
    if type(input_str) == unicode:
        nkfd_form = unicodedata.normalize('NFKD', input_str)
        only_ascii = nkfd_form.encode('ASCII', 'ignore')
    else:
        only_ascii = input_str
    return only_ascii

def prettifyString(input_str):
    res = removeAccents(input_str)
    res = res.replace('"','')
    res = '"'+res+'"'
    if res == '""' or res == '" "' or res == '" "':
        res = '\\N'
    return res

def keys_to_remove(list_of_keys, the_dict):
    for key in list_of_keys:
        if key in the_dict:
            del the_dict[key]

def parseTitle(value):
    if isinstance(value, basestring):
        res = removeAccents(value)
    else:
        res = '\\N'
    return res

def parseArtistName(value):
    if isinstance(value, basestring):
        value = removeAccents(value)
        if '(' in value:
            value = value.split('(')[0].strip(' ')
        res = '\"'+value.lower()+'\"'
    else:
        res = '\\N'
    return res

def indexContainingSubstring(the_list, value):
    for i, s in enumerate(the_list):
        if s in value:
            return i
    return 999

def parseLscLink(auction):
    try:
        tmp = auction.findAll("div",{"lsc_link"})[0].findAll('a')[0]['href']
        auction_link = prettifyString(tmp)
        regex = re.compile("(?:(?m)/artist/([0-9]{1,})/([A-Za-z\\-]{1,})/lot/pasts/([0-9]{1,}))")
        tmp = regex.findall(auction_link)[0]
        auction_id = prettifyString(tmp[2])
        artist_id = prettifyString(tmp[0])
        artist_name = prettifyString(tmp[1].replace('-', ' '))
        res = {'auction_id':auction_id, 'auction_link':auction_link, 
               'artist_id':artist_id, 'artist_name':artist_name}
    except:
        res = '\\N'
    return res

def parseLscTitle(auction):
    try:
        tmp = auction.findAll("div",{"lsc_title"})[0].get_text().strip().split('\n')[0]
        if type(tmp) == unicode:
            res = {'title': prettifyString(tmp)}
        elif type(tmp) == list and len(tmp) > 1:
            res = {'title':prettifyString(tmp[0]), 'year_of_creation':prettifyString(res[-1].replace(' ','').replace('(', '').replace(')',''))}
        else:
            res = '\\N'
    except:
        res = '\\N'
    return res

def parseCategory(value):
    value = value.lower()
    category = ['drawing-watercolor', 'drawing', 'painting', 'photography', 
                'print-multiple', 'print', 'sculpture', 'sculpture-volume']
    index = indexContainingSubstring(category, value)
    try:
        res = prettifyString(category[index])
    except:
        res = '\\N'
    return res

def parseSize(value):
    #size_regex = re.compile("(?:(?m)([0-9]{1,})(?:\\ [0-9]/[0-9]){0,}(?:\\ x){0,}(?:\\ ([0-9]{1,})){0,}(?:\\ [0-9]/[0-9]){0,}\\ cm)")
    # debuggex: ([0-9]+)(?: [0-9]/[0-9])*(?: x)*(?: ([0-9]+))*(?: [0-9]/[0-9])* in
    try:
        tmp = value.strip().split('x')
        tmp = [el.strip().replace(' ','').replace('in','').replace('cm','') for el in tmp]
        if len(tmp) == 1:
            res = [prettifyString(tmp[0]), '\\N']
        elif len(tmp) == 2:
            res = [prettifyString(tmp[0]), prettifyString(tmp[1])]
        else:
            res = '\\N'
    except:
        res = '\\N'
    return res

def parseMedium(value):
    value = value.lower().strip().replace(' ','')
    medium_first = ['etching', 'engraving', 'litograph', 'lithograph']
    medium = ['aluminium', 'aluminum', 'acrylic', 'aquatec', 'aquatint', 'ballpoint', 'bronze', 'burin', 'bas-relief', 'bromoil', 
              'caborundum', 'ceramic', 'chalk', 'charcoal', 'clay', 'collage', 'copper', 'crayon',
              'drawing', 'drypoint', 'earthenware', 'gilded', 'graphite', 'glass', 'gold', 'gouache', 
              'heliography', 'ink', 'linocut', 'marble', 'medal', 'metal', 'mixed', 'molten', 
              'object', 'offset', 'oil', 'poster', 'pencil', 'perspex', 'plaster', 'porcelain', 'plastic', 'pastel',
              'relief', 'resin', 'screenprint', 'serigraph', 'silkscreen', 'silver', 'stencil', 'stone', 
              'tapestry', 'tempera', 'terracotta', 
              'wax', 'wash', 'watercolour', 'woodcut', 'xilograph', 'xylograph']
    medium_last = ['painting', 'print', 'photograph', 'pen', 'sculpture']
    medium = medium_first+medium+medium_last
    # aquatec is acrylic and so on
    index = indexContainingSubstring(medium, value)
    try:
        res = prettifyString(medium[index])
    except:
        res = '\\N'
    return res

def parseLscDetails(auction):
    try:
        tmp = auction.findAll("div", {"lsc_details"})[0].get_text().strip().split('\n')
        if len(tmp) == 4:
            category = parseCategory(tmp[0])
            medium = parseMedium(tmp[2])
            size = parseSize(tmp[3])
        elif len(tmp) == 5:
            category = parseCategory(tmp[0])
            medium = parseMedium(tmp[3])
            size = parseSize(tmp[4])
        else:
            res = '\\N'
            return res
        if len(size) == 1:
            size_width = size[0]
            size_length = '\\N'
        else:
            size_width = size[0]
            size_length = size[1]
        if category != '\\N' and medium != '\\N' and size != '\\N':
            res = {'category':category, 'medium':medium, 'size_width':size_width, 'size_length':size_length}
        else:
            res = '\\N'
    except:
        res = '\\N'
    return res

def parseLscAdjud(auction):
    try:
        tmp = auction.findAll("div", {"lsc_adjud"})[0].get_text().strip().split('\n')[-1].strip()
        price_regex = re.compile("(?:(?m)\\$([0-9,]{1,})|(not\\ communicated)|(Withdrawn)|(Lot\\ not\\ sold))")
        price_match = price_regex.findall(tmp)[0]
        price_match = [val for val in price_match if val != '']
        tmp = price_match[0]
        tmp = tmp.replace(',','')
        try:
            tmp = float(tmp)
            tmp = str(tmp)
        except:
            tmp = '\\N'
        tmp = prettifyString(tmp)
        res = {'hammer_price': tmp}
    except:
        res = '\\N'
    return res

def parseLscAuctioneer(auction):
    try:
        tmp = auction.findAll("div", {"lsc_auctioneer"})[0].get_text().strip().split('\n')
        if len(tmp) == 1:
            res = {'auction_house_name':prettifyString(tmp[0].strip().replace(',', ''))}
        else:
            res = {'auction_house_name':prettifyString(tmp[0].strip().replace(',', '')), 'auction_house_city':prettifyString(tmp[1].strip().replace('  ', ''))} 
    except:
        res = '\\N'
    return res

def parseLscCountry(auction):
    try:
        tmp = auction.findAll("div", {"lsc_country"})[0].get_text().strip().split('\n')
        auction_house_country = prettifyString(tmp[0].replace(',',''))
        tmp = tmp[1].replace('  ','').split('-')
        sales_date_day = prettifyString(tmp[0])
        sales_date_month = prettifyString(tmp[1])
        sales_date_year = prettifyString(tmp[2])
        res = {'auction_house_country':auction_house_country, 'sales_date_day':sales_date_day, 'sales_date_month':sales_date_month, 'sales_date_year':sales_date_year} 
    except:
        res = '\\N'
    return res

def parseLscImage(auction):
    try:
        img_link = prettifyString(auction.findAll("div",{"lsc_img"})[0].findAll('img',{'class':'img_repro'})[0]['src'])
        res = {'img_link':img_link}
    except:
        res = '\\N'
    return res

def parseLscEstimate(auction):
    try:
        tmp = auction.findAll("div",{"lsc_estimate"})[0].get_text().split('\n')[2].strip()
        range_regex = re.compile("(?:(?m)\\$([0-9,]{1,}).(?:[A-Za-z\\-\\ ]{1,}).\\$([0-9,]{1,}))")
        range_match = range_regex.findall(tmp)
        low_est = range_match[0][0].replace(',','')
        high_est = range_match[0][1].replace(',','')
        res = {'low_estimate':low_est, 'high_estimate':high_est}
    except:
        res = '\\N'
    return res

def fieldCsvLineList(value_dict, entry, fields_dict, csv_line_list):
    if type(entry) == int:
        field_name = value_dict.keys()[entry]
        field_index = fields_dict[field_name]
        csv_line_list[field_index] = value_dict[field_name]
    elif type(entry) == list:
        [fieldCsvLineList(value_dict, single_entry, fields_dict, csv_line_list) for single_entry in entry]
    return None

def parseTag(auction, tag_name, csv_line_list):
    '''
    tag names 
    minimum_tag_names_to_scrape = ['lsc_title', 'lsc_details', 'lsc_adjud', 'lsc_auctioneer', 
                                     'lsc_country', 'lsc_link']
    optional_tag_names_to_scrape = ['lsc_estimate ', 'lsc_image']
    csv line list elements:
    '''
    minimum_fields_dict = {'auction_id':0, 'auction_link':1, 'title':2, 'artist_id':3, 'artist_name':4, 
                           'category':5, 'medium':6, 'size_width':7, 'size_length':8, 
                           'sales_date_day':9, 'sales_date_month':10, 'sales_date_year':11, 
                           'auction_house_name':12, 'auction_house_city':13, 'auction_house_country':14, 
                           'hammer_price':15}
    optional_fields_dict = {'year_of_creation':16, 'low_estimate':17, 
                            'high_estimate':18, 'img_link':19}
    if tag_name == 'lsc_title':
        value = parseLscTitle(auction)
        if value != '\\N':
            if len(value) == 1:
                fieldCsvLineList(value, 0, minimum_fields_dict, csv_line_list)
                return True
            elif len(value) == 2:
                fieldCsvLineList(value, [0,1], dict(minimum_fields_dict.items()+optional_fields_dict.items()), csv_line_list)
                return True
            else:
                return False
        else:
            return False
    if tag_name == 'lsc_details':
        value = parseLscDetails(auction)
        if value != '\\N':
            if len(value) == 3:
                fieldCsvLineList(value, [0,1,2], minimum_fields_dict, csv_line_list)
                return True
            elif len(value) == 4:
                fieldCsvLineList(value, [0,1,2,3], minimum_fields_dict, csv_line_list)
                return True
            else:
                return False
        else:
            return False
    if tag_name == 'lsc_adjud':
        value = parseLscAdjud(auction)
        if value != '\\N':
            fieldCsvLineList(value, 0, minimum_fields_dict, csv_line_list)
            return True
        else:
            return False
    if tag_name == 'lsc_auctioneer':
        value = parseLscAuctioneer(auction)
        if value != '\\N':
            fieldCsvLineList(value, [0,1], minimum_fields_dict, csv_line_list)
            return True
        else:
            return False
    if tag_name == 'lsc_country':
        value = parseLscCountry(auction)
        if value != '\\N':
            fieldCsvLineList(value, [0,1,2,3], minimum_fields_dict, csv_line_list)
            return True
        else:
            return False
    if tag_name == 'lsc_link':
        value = parseLscLink(auction)
        if value != '\\N':
            fieldCsvLineList(value, [0,1,2,3], minimum_fields_dict, csv_line_list)
            return True
        else:
            return False
    if tag_name == 'lsc_estimate':
        value = parseLscEstimate(auction)
        if value != '\\N':
            fieldCsvLineList(value, [0,1], optional_fields_dict, csv_line_list)
            return True
        else:
            return False
    if tag_name == 'lsc_image':
        value = parseLscImage(auction)
        if value != '\\N':
            fieldCsvLineList(value, 0, optional_fields_dict, csv_line_list)
            return True
        else:
            return False
    return False

def readSqlSelectIntoPandasDf(sql_command):
    ''' Read a select statement into a panda dataframe '''
    mysql_cn= mdb.connect('localhost', 'root','','abstrart_db')
    df = psql.frame_query(sql_command, con=mysql_cn)
    mysql_cn.close()
    return df

# First, define the directory with the html files
file_dir = '/Users/daniel/insight/artprice_html_files/'
# Second, Get the links for a given artist
artists = readSqlSelectIntoPandasDf('select link from pantheon')['link']
# TODO: erase this line, just needed for now.
artists = artists[0:182]
# Third, define where to save all auctions
csv_fh = open('/Users/daniel/insight/artprice_data/auctions.txt', 'w')
# Define useful objects for scraping
auction_id_regex = re.compile("(?:(?m)pasts/([0-9]{1,}))")
npages_regex = re.compile("(?:(?m)amp;p=([0-9]{0,}))")
minimum_tag_names_to_scrape = ['lsc_title', 'lsc_details', 'lsc_adjud', 'lsc_auctioneer', 
                               'lsc_country', 'lsc_link']
optional_tag_names_to_scrape = ['lsc_estimate ', 'lsc_image']
minimum_fields_dict = {'auction_id':0, 'auction_link':1, 'title':2, 'artist_id':3, 'artist_name':4, 
                       'category':5, 'medium':6, 'size_width':7, 'size_length':8, 
                       'sales_date_day':9, 'sales_date_month':10, 'sales_date_year':11, 
                       'auction_house_name':12, 'auction_house_city':13, 'auction_house_country':14, 
                       'hammer_price':15}
optional_fields_dict = {'year_of_creation':16, 'low_estimate':17, 'high_estimate':18, 'img_link':19}
# START SCRAPING ALL AUCTIONS FOR EACH ARTIST PAGE
for artist_link in artists:
    artist_id = artist_link.split('/')[0]
    artist_name = artist_link.split('/')[1]
    try:
        # open the artist page with all the auction info on first page
        file_name = artist_name.replace('-','')+'_p'+str(1)+'.html'
        artist_html_p1_fh = open(os.path.join(file_dir, file_name), 'r')
        artist_html_p1 = artist_html_p1_fh.read()
        npages_match = npages_regex.findall(artist_html_p1)
        npages_match = max([int(page) for page in npages_match])
        print 'getting the links for %s from %s pages' %(artist_name, npages_match)
        auction_count = 0
        for page_number in range(1, npages_match+1):
            print 'downloading links for artist %s page %s' %(artist_name, page_number)
            file_name = artist_name.replace('-','')+'_p'+str(page_number)+'.html'
            full_name = os.path.join(file_dir, file_name)
            artist_html_fh =  open(os.path.join(file_dir, file_name), 'r')
            artist_html = artist_html_fh.read() 
            soup = BeautifulSoup(artist_html)
            auctions = soup.findAll("div", {"lot_sml_container"})
            for auction in auctions:
                auction_count += 1
                csv_line_list = ['\\N' for i in range(0, len(minimum_fields_dict)+len(optional_fields_dict))]
                for tag_name in minimum_tag_names_to_scrape:
                    min_tag_flag = False
                    try:
                        res = parseTag(auction, tag_name, csv_line_list)
                        if res == False:
                            print '(One Min Tag Failed) auction %s, for artist %s, page %s, did not work' %(auction_count, artist_name, page_number)
                            min_tag_flag = True
                            break
                        elif res == True:
                            continue
                        else:
                            print '(Sthg Odd!) auction %s, for artist %s, page %s, did not work' %(auction_count, artist_name, page_number)
                            min_tag_flag = True
                            break
                    except:
                        print '(parseTag False) auction %s, for artist %s, page %s, did not work' %(auction_count, artist_name, page_number)
                        min_tag_flag = True
                        break
                for tag_name in optional_tag_names_to_scrape:
                    try:
                        res = parseTag(auction, tag_name, csv_line_list)
                    except:
                        continue
                if min_tag_flag == False:
                    csv_fh.write(','.join(csv_line_list)+'\n')
    except:
        print '(FirstTryFailed) auction %s, for artist %s, page %s, did not work' %(auction_count, artist_name, page_number)
csv_fh.close()