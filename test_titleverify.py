__author__ = 'freak'
from domainanalysis import CrawlImproperDomains as domainanalysis
from urlparse import urlparse
from BeautifulSoup import BeautifulSoup
from verification import Verify
import re
import urllib2

url = 'http://samwinebaum.blogspot.de/2014/06/review-salomon-s-lab-sense-shorts-are.html'

def get_url_pattern(url):
        url_patterns = []
        parsed = urlparse(url)
        #print(parsed)
        pattern = parsed.netloc
        p = pattern.split('.')
        pattern = '\.'.join(p)
        pattern = pattern + parsed.path
        return pattern

def verify_multiple_article_hrefs(url):
    page = urllib2.urlopen(url)
    raw_html = page.read()
    bs = BeautifulSoup(raw_html)
    pattern = get_url_pattern(url)
    a_tag = bs.findAll('a', href=re.compile("(" + pattern + ")"))#TODO:Write the right regex for all blogs
    if a_tag is None:
        a_tag = bs.findAll('a', href=re.compile("(/blogs/)"))

    cnt = 0
    text_vals = []
    print(a_tag)
    for i in a_tag:
        text_vals.append(i.findAll(text=True)) #TODO: Filter the number of links and verify
        cnt += 1
    print(text_vals)
    if cnt == 0:
        return False
    else:
        return True


verify_multiple_article_hrefs(url)