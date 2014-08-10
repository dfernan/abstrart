#!/usr/bin/env python

import math
import mechanize
import pickle
import re
import string
import sys

start = int(sys.argv[1])
print '%s' %(start)
end = int(sys.argv[2])
print '%s' %(end)
browser = mechanize.Browser()
artprice_url = 'http://www.artprice.com/identity'
browser.open(artprice_url)
browser.select_form(nr = 0)
browser.form['login'] = 'dfernan@gmail.com'
browser.form['pass'] = 'ledc1182'
browser.submit()
letters = string.uppercase
letters = list(letters)
letters1 = letters[start:end]
prefix_url = 'http://www.artprice.com/artists/directory/'
artists_list = []
artists_regex = re.compile("(?:(?m)href=\"/artist/([0-9]{1,}/[A-Za-z\\-]{1,})\"\\>)")
max_regex = re.compile("(?:(?m)artists\\ index\\ includes\\ ([0-9,]{0,})\\ artists)")
l1_letter_tm1 = '0'
l1_max = 10
for l1 in letters1:
    for l2 in letters:
        i=1
        while i <= l1_max:
            tmp_url = '%s%s/%s?page=%s' %(prefix_url, l1, l2, i)
            print tmp_url
            artists_page = browser.open(tmp_url).read()
            artists_match = artists_regex.findall(artists_page)
            artists_list.extend(artists_match)
            if l1_letter_tm1 != l1:
                max_match = float(max_regex.findall(artists_page)[0].replace(',',''))
                l1_max = int(math.ceil(max_match/100.0))
                print l1_max
            if l1_max == 0:
                l1_max = 10
                break
            i = i+1
pickle.dump(artists_list, open('/Users/daniel/insight/artprice_data/artists_links_%s_%s.p' %(start,end),'w'))
#artists_dict.     dupdate({artist.split('/')[0]:artist.split('/')[1] for artist in artists_match})
#artists_page = browser.open('http://www.artprice.com/artists/directory/C/A?page=1').read()
# for later
# browser.open('http://www.artprice.com/artist/466622/eric-cabanas/lot/pasts/2/Print-Multiple/5839800/la-place-du-commerce?p=1&iso3=USD').read()