#!/usr/bin/env python

from bs4 import BeautifulSoup
import urllib2

tmp_url = 'https://artsy.net/galleries'
galleries_site = urllib2.urlopen(tmp_url).read() 
soup = BeautifulSoup(galleries_site)
a = soup.findAll("li", {"a-to-z-item"})
gallery_contacts_links = []
for element in a:
    b = element.findAll('a',href=True)[0]
    print b['href']
    gallery_contacts_links.append(b['href'])
prefix_url = 'https://artsy.net'
suffix_url = '/contact'
gallery_contacts_links2 = ['%s%s%s' %(prefix_url, element, suffix_url) for element in gallery_contacts_links]