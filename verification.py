__author__ = 'freak'
from goose import Goose
import urllib2
import stringops
from xpathops import element2path
import re
from BeautifulSoup import BeautifulSoup
from urlparse import urlparse


class Verify:
    def __init__(self):
        self.goose = Goose({'enable_image_fetching':False})

    def extract_html(self, url):
        page = urllib2.urlopen(url)
        raw_html = page.read()
        return raw_html

    def verify_article(self, url, val):
        raw_html = self.extract_html(url)
        ext = self.goose.extract(raw_html=raw_html)
        print('title: ' + ext.title)
        istitleverified = self.verify_article_title(ext.title, url)
        return istitleverified

    def verify_article_title(self, article_title, url):
        #Using goose extract title. Then go to the blog home page and extract the text and
        #check for String with same as title
        url_to_check = 'http:/'
        checked = False
        titlepresent = False
        i = 0
        url_split = url.split('/')

        while url_split[0] in ['', 'http:', 'https:']:
            del url_split[0]

        url_split = filter(None, url_split)

        if len(url_split) > 1:
            url_split.pop()

        print(url_split)
        while not checked:
            url_to_check = url_to_check + '/' + url_split[i]

            if i == len(url_split)-1:
                checked = True
            i += 1

            ext1 = self.goose.extract(url_to_check)
            raw_html = ext1.raw_html.decode('utf-8', 'ignore')

            if article_title in raw_html: #TODO: Handel &nbsps and other utf-8 characters
                checked = True
                titlepresent = True
            else:
                titlepresent = False

        return titlepresent

    def verify_comments(self, tree, comments=None, root_paths=None):
        comment_root_paths = []
        if root_paths is not None:
            comment_root_paths = root_paths
        elif root_paths is None:
            for com in comments:
                comment_root_paths.append(element2path(tree, com.root_node))

        comment_root_paths, common_beg, diff_middle, common_end = stringops.find_difference_inside(comment_root_paths)

        if diff_middle.isdigit():
            print 'Comments: regularity found'
            return True
        else:
            return False

    def verify_multiple_articles(self, mulart, url, tree):
        mul_art_root_paths = []
        multiple_article_text = []

        for mul in mulart:
            multiple_article_text.append(mul.full_text.encode('utf-8', 'ignore'))
            mul_art_root_paths.append(element2path(tree, mul.root_node))

        print('multiple article text: ')
        print(multiple_article_text)
        struct_verified = self.verify_multiple_articles_pagetags_structure(mul_art_root_paths)
        href_verified = self.verify_multiple_article_hrefs(url)
        sim_text_verified = self.verify_similar_text(multiple_article_text, url)
        if struct_verified and href_verified and sim_text_verified:
            return True
        else:
            return False

    def verify_multiple_articles_pagetags_structure(self, multiple_articles):
        print(multiple_articles)
        comment_root_paths, common_beg, diff_middle, common_end = stringops.find_difference_inside(multiple_articles)

        if diff_middle.isdigit():
            print 'Multiple article page: regularity found'
            return True
        else:
            return False

    def get_url_pattern(self, url):
        url_patterns = []
        parsed = urlparse(url)
        #print(parsed)
        pattern = parsed.netloc
        p = pattern.split('.')
        pattern = '\.'.join(p)
        pattern = pattern + parsed.path
        return pattern

    def verify_multiple_article_hrefs(self, url):
        raw_html = self.extract_html(url)
        bs = BeautifulSoup(raw_html)
        pattern = self.get_url_pattern(url)
        a_tag = bs.findAll('a', href=re.compile("(" + pattern + ")"))
        if len(a_tag) == 0:
            a_tag = bs.findAll('a', href=re.compile("(/blogs/)"))

        if len(a_tag) > 5: #Choosen 5 as a random number. The basic idea is to find if the page contains many article
            return True     # to decide to its a blog-home page or not. If its a home page, then there will be atleast more than 5
        else:               #related links. If its a article page, then number of related links will be less than 5.
            return False

    def verify_similar_text(self, multiple_article_text, url):
        sametextnotpresent = True
        parsed = urlparse(url)
        path_split = []
        domain_to_check = parsed.scheme + '://' + parsed.netloc
        print('domain to check: ' + domain_to_check)
        if len(parsed.path) > 1:
            path_split = str(parsed.path).split('/')
            path_split = filter(None, path_split)
            path_split.pop()

        if len(path_split) > 0:#Implies the url is not home page. No need to check for similar text in home page
            goose = Goose({'enable_image_fetching': False})
            article = goose.extract(domain_to_check)
            article_text = article.cleaned_text
            for s in multiple_article_text:
                if s in article_text.encode('utf-8', 'ignore'):
                    sametextnotpresent = False

            #If not present in main domain, check in subdomains for similar text
            #commented, because if the similar text is a template text, it should be present in the main domain too
            #if sametextnotpresent and len(path_split) > 0:
            #    for path in path_split:
            #        goose = Goose()
            #        domain_to_check = domain_to_check + '/' + path
            #        article = goose.extract(domain_to_check)
            #        article_text = article.cleaned_text
            #        for s in multiple_article_text:
            #            if s in article_text.encode('utf-8', 'ignore'):
            #                sametextnotpresent = False
            #                break

        return sametextnotpresent


    def verify_url_domain(self, url, ver_dom):
        parsed = urlparse(url)
        domain_to_check = parsed.scheme + '://' + parsed.netloc
        checked = False
        path_split = []
        if len(parsed.path) > 1:
            path_split = str(parsed.path).split('/')
            path_split = filter(None, path_split)
        print(domain_to_check)
        if domain_to_check in ver_dom:
            checked = True
        elif len(path_split) > 0:
            for path in path_split:
                domain_to_check = domain_to_check + '/' + path
                if domain_to_check in ver_dom:
                    checked = True

        return checked


if __name__ == '__main__':
    ver = Verify()
    url = 'http://blogs.independent.co.uk'
    vals = ['/html/body/ul[3]/li/div/p[1]', '/html/body/ul[3]/li/div/p[1]/span[1]', '/html/body/ul[3]/li/div/p[1]/span[3]', '/html/body/ul[3]/li/div/p[1]/span[5]', '/html/body/ul[3]/li/div/p[2]', '/html/body/ul[3]/li/div/p[2]/span[1]']
    #vals = ['/html/body/div[3]', '/html/body/div[4]/div']
    res = ver.verify_multiple_articles_pagetags_structure(vals)
    print(res)