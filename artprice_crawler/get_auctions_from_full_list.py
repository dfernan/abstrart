#!/usr/bin/env python

from bs4 import BeautifulSoup
import mechanize
import pickle
import re
import unicodedata

def loginToArtPrice():
    browser = mechanize.Browser()
    artprice_url = 'http://www.artprice.com/identity'
    browser.open(artprice_url)
    browser.select_form(nr = 0)
    browser.form['login'] = 'dfernan@gmail.com'
    browser.form['pass'] = 'ledc1182'
    browser.submit()
    return browser

def keys_to_remove(list_of_keys, the_dict):
    for key in list_of_keys:
        if key in the_dict:
            del the_dict[key]
  
def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nkfd_form.encode('ASCII', 'ignore')
    return only_ascii

def parseTitle(value):
    if isinstance(value, basestring):
        res = remove_accents(value)
    else:
        res = 'NULL'
    return res

def parseArtistName(value):
    if isinstance(value, basestring):
        value = remove_accents(value)
        if '(' in value:
            value = value.split('(')[0].strip(' ')
        res = '\"'+value.lower()+'\"'
    else:
        res = 'NULL'
    return res

def index_containing_substring(the_list, value):
    for i, s in enumerate(the_list):
        if s in value:
            return i
    return 999

def parseCategory(value):
    value = value.lower()
    category = ['drawing-watercolor', 'drawing', 'painting', 'photography', 
                'print-multiple', 'print', 'sculpture', 'sculpture-volume']
    index = index_containing_substring(category, value)
    try:
        res = category[index]
    except:
        res = 'NULL'
    return res

def parseSize(value):
    size_regex = re.compile("(?:(?m)([0-9]{1,})(?:\\ [0-9]{1,}/[0-9]{1,}){0,1}\\ in\\ x\\ ([0-9]{1,}))")
    try:
        size_match = size_regex.findall(value)[0]
        res = [int(size_match[0]), int(size_match[1])]
    except:
        res = 'NULL'
    return res

def parseSalesDate(value):
    try:
        value = value.split('-')
        res = [value[0], value[1], value[2]]
    except:
        res = 'NULL'
    return res
    
def parseAuctionHouse(value):
    try:
        value_list = value.split('\n')
        res = [value_list[0], value_list[-2], value_list[-1], value]
    except:
        res = 'NULL'
    return res

def parseHammerPrice(field_value):
    try:
        price_regex = re.compile("(?:(?m)\\$([0-9,]{1,})|(not\\ communicated)|(Lot\\ not\\ sold))")
        price_match = price_regex.findall(field_value)[0]
        price_match = [val for val in price_match if val != '']
        res = price_match[0]
        res = res.replace(',','')
    except:
        res = 'NULL'
    return res

def parseDateOfCreation(field_value):
    try:
        year_of_creation_regex = re.compile("(?:(?m)^\\d{1,4}$)")
        res = year_of_creation_regex.findall(field_value)[0]
    except:
        res = 'NULL'
    return res

def parseMedium(value):
    value = value.lower()
    medium_first = ['etching', 'engraving', 'litograph']
    medium = ['aluminium', 'aluminum', 'acrylic', 'aquatec', 'aquatint', 'ballpoint', 'bronze', 'burin', 'bas-relief', 'bromoil', 
              'caborundum', 'ceramic', 'chalk', 'charcoal', 'clay', 'collage', 'copper', 'crayon',
              'drawing', 'drypoint', 'earthenware', 'gilded', 'graphite', 'glass', 'gold', 'gouache', 
              'heliography', 'ink', 'linocut', 'marble', 'medal', 'metal', 'mixed', 'molten', 
              'object', 'offset', 'oil', 'poster', 'pencil', 'perspex', 'plaster', 'porcelain', 'plastic', 'pastel'
              'relief', 'resin', 'screenprint', 'serigraph', 'silkscreen', 'silver', 'stencil', 'stone', 
              'tapestry', 'tempera', 'terracotta', 
              'wax', 'wash', 'watercolour', 'woodcut', 'xilograph']
    medium_last = ['painting', 'print', 'photograph', 'pen', 'sculpture']
    medium = medium_first+medium+medium_last
    # aquatec is acrylic and so on
    index = index_containing_substring(medium, value)
    try:
        res = medium[index]
    except:
        res = 'NULL'
    return res
    
def parseDistinguishingMarks(value):
    value = value.lower()
    value = value.replace('lower','signed')
    value = value.replace('right','signed')
    value = value.replace('left','signed')
    if 'signed' in value:
        distinguishing_marks_signed = 'signed'
    else:
        distinguishing_marks_signed = 'NULL'
    try:
        regex = re.compile("(?:(?m)#([0-9]{1,})/([0-9]{1,}))")
        match_array = regex.findall(value)[0]
        distinguishing_marks_print_number = match_array[0]
        distinguishing_marks_total_print = match_array[1]
    except:
        distinguishing_marks_print_number = 'NULL'
        distinguishing_marks_total_print = 'NULL'
    res =  [distinguishing_marks_print_number, distinguishing_marks_total_print, distinguishing_marks_signed, value]
    return res
        
def parseField(field_name, field_value, csv_line_list):
    '''
    csv line list elements:
    Minimum Required
    0:'title', 1:'artist_id', 
    2:'artist_name', 3:'category', 
    4:'size_width', 5:'size_length', 6:'size_area', 
    7:'sales_date_day', 8:'sales_date_month', 9:'sales_date_year', 
    10:'auction_house_name', 11:'auction_house_address', 12:'auction_house_city', 13:'auction_house_country', 
    14:'hammer_price'
    Optional
    15:'medium', 16:'year_of_creation', 
    17:'distinguishing_marks_print_number', 18: 'distinguishing_marks_total_prints', 19:'distinguishing_marks_signed', 20:'distinguishing_marks_text' 
    21:'low_estimate', 22:'high_estimate', 23:'image_link'
    field_names 
    Minimum required
    ['Title', 'Artist', 'Category', 'Size', 'Sales date', 'Auction house','Hammer price']
    Optional
    ['Date of Creation', 'Medium', 'Distinguishing marks', 'Low estimate', 'High Estimate']
    '''
    if field_name.lower() == 'title':
        value = parseTitle(field_value)
        if value != 'NULL':
            csv_line_list[0] = value
            return True
        else:
            return False
    if field_name.lower() == 'artist':
        value = parseArtistName(field_value)
        if value != 'NULL':
            csv_line_list[2] = value
            return True
        else:
            return False
    if field_name.lower() == 'category':
        value = parseCategory(field_value)
        if value != 'NULL':
            csv_line_list[3] = value
            return True
        else:
            return False
    if field_name.lower() == 'size':
        value = parseSize(field_value)
        if value != 'NULL':
            csv_line_list[4] = value[0]
            csv_line_list[5] = value[1]
            csv_line_list[6] = value[0]*value[1]
            return True
        else:
            return False
    if field_name.lower() == 'sales date':
        value = parseSalesDate(field_value)
        if value != 'NULL':
            csv_line_list[7] = value[0]
            csv_line_list[8] = value[1]
            csv_line_list[9] = value[2]
            return True
        else:
            return False
    if field_name.lower() == 'auction house':
        value = parseAuctionHouse(field_value)
        if value != 'NULL':
            csv_line_list[10] = value[0]
            csv_line_list[11] = value[1]
            csv_line_list[12] = value[2]
            csv_line_list[13] = value[3]
            return True
        else:
            return False
    if field_name.lower() == 'medium':
        value = parseMedium(field_value)
        if value != 'NULL':
            csv_line_list[15] = value
            return True
        else:
            return False
    if field_name.lower() == 'date of creation':
        value = parseDateOfCreation(field_value)
        if value != 'NULL':
            csv_line_list[16] = value
            return True
        else:
            return False
    if field_name.lower() == 'distinguishing marks':
        value = parseCategory(field_value)
        if value != 'NULL':
            csv_line_list[17] = value[0]
            csv_line_list[18] = value[1]
            csv_line_list[19] = value[2]
            csv_line_list[20] = value[3]
            return True
        else:
            return False
    if field_name.lower() == 'hammer price':
        value = parseHammerPrice(field_value)
        if value != 'NULL':
            csv_line_list[14] = value
            return True
        else:
            return False
    if field_name.lower() == 'low estimate':
        value = parseHammerPrice(field_value)
        if value != 'NULL':
            csv_line_list[21] = value
            return True
        else:
            return False
    if field_name.lower() == 'high estimate':
        value = parseHammerPrice(field_value)
        if value != 'NULL':
            csv_line_list[22] = value
            return True
        else:
            return False
    return False

# First, Login to artprice.com
browser = loginToArtPrice()

# Second, Get the Link for all auctions
csv_fh = open('/Users/daniel/insight/artprice_data/auctions.txt', 'w')
auctions_links = pickle.load(open('/Users/daniel/insight/artprice_data/paintings_links.p', 'rb'))
lits_of_keys_to_remove = [artist_id for (artist_id, value) in auctions_links.items() if value=='NULL']
keys_to_remove(lits_of_keys_to_remove, auctions_links)
n_auctions = sum(len(v) for v in auctions_links.itervalues())
print 'The number of auctions to parse is %s' %(n_auctions)
auctions_links = dict((k, auctions_links[k]) for k in ('166760', '62600', '6866'))

# Third, Scrape each field_name and field_value for a given auction
prefix_url = 'http://www.artprice.com'
minimum_field_names_to_scrape = ['title', 'artist', 'category', 'size', 'auction house', 'sales date','hammer price']
optional_field_names_to_scrape = ['date of Creation', 'medium', 'distinguishing marks', 'low estimate', 'high Estimate']
minimum_field_names_to_save = ['title', 'artist_id', 'artist_name', 'category',
                               'size_width', 'size_length', 'size_area', 'sales_date_day', 'sales_date_month', 'sales_date_year', 
                               'auction_house_name', 'auction_house_address', 'auction_house_city', 'auction_house_country', 
                               'hammer_price']
optional_field_names_to_save = ['medium', 'year_of_creation', 
                                'distinguishing_marks_print_number', 'distinguishing_marks_total_prints', 'distinguishing_marks_signed', 'distinguishing_marks_text',
                                'low_estimate', 'high_estimate', 'image_link', 'auction_id', 'auction_link']
n_fields_to_save = len(minimum_field_names_to_save+optional_field_names_to_save)
auction_id_regex = re.compile("(?:(?m)pasts/([0-9]{1,}))")
painting_image_link_regex = re.compile("(?:(?m)\"(http://imgprivate2.artprice.com/lot/.{0,}\")\\ style=\"cursor:pointer;\")")
auction_count = 0
for artist_id in auctions_links:
    for auction_link in auctions_links[artist_id]:
        auction_count += 1
        if auction_count%100 == 0:
            print 'Saving auction %s' %(auction_count)
        csv_line_list = ['NULL' for i in range(0, n_fields_to_save)]
        csv_line_list[1] = artist_id
        tmp_url = '%s%s' %(prefix_url, auction_link)
        try:
            auction_id = int(auction_id_regex.findall(auction_link)[0])
            csv_line_list[-2] = auction_id
            csv_line_list[-1] = tmp_url
        except:
            print 'Step 1: Could not parse auction number %s' %(auction_count)
        auction_site = browser.open(tmp_url).read()
        try:
            image_link = painting_image_link_regex.findall(auction_site)[0]
        except:
            pass
        soup = BeautifulSoup(auction_site)
        a = soup.findAll("div", {"item_title"})
        b = soup.findAll("div", {"item_value"})
        for i in range(0, len(a)):
            try:
                field_name = a[i].get_text().strip().replace('  ', '').replace('\n','').replace('Location', '').replace('/','').lower()
                if field_name in set(minimum_field_names_to_scrape):
                    if field_name.lower() != 'auction house':
                        field_value = b[i].get_text().strip()
                    else:
                        field_value = b[i].renderContents().replace('  ', '').replace('\n','').replace('<br/>','\n')
                    parse_min_status = parseField(field_name, field_value, csv_line_list)
                    if parse_min_status == False:
                        print 'Could not parse %s auction number %s %s' %(field_name, auction_count)
                        break
                elif field_name in set(optional_field_names_to_scrape):
                    try:
                        field_value = b[i].get_text().strip()
                        parse_optional_status = parseField(field_name, field_value, csv_line_list)
                    except:
                        continue
                else:
                    continue
            except:
                print 'Could not parse auction number %s' %(auction_count)
        csv_fh.write('\t'.join([str(el) for el in csv_line_list])+'\n')
browser.close()
csv_fh.close()