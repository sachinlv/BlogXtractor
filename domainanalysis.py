__author__ = 'freak'

from sd_algorithm import SDAlgorithm
from BeautifulSoup import BeautifulSoup
import happybase
import urllib2
import re
from urlparse import urlparse
from verification import Verify
from xpathops import element2path


class CrawlImproperDomains():
    def __init__(self):
        self.connection = None
        self.domains_table = None
        self.sd = None #SDAlgorithm()
        self.current_domain = ''

    def database_connect(self, tablename):
        self.connection = happybase.Connection(host='127.0.0.1', port=9090)
        self.domains_table = self.connection.table(tablename)

    def save_domain_verification_result(self, verification_result):
        self.database_connect('verifieddomains')
        rows = self.domains_table.scan()
        row_count = sum(1 for _ in rows)
        print('result: ' + str(verification_result))
        for key in verification_result:
            urlstr = key
            articletype = verification_result[key][0]
            path_dict = verification_result[key][1]
            density_avg = verification_result[key][2]
            row_count = row_count + 1
            rowkey = 'r' + str(row_count)
            self.domains_table.put(rowkey, {'domain:domaintested': self.current_domain, 'domain:urltested': urlstr, 'article:type':articletype, 'article:schema': str(path_dict), 'article:density': str(density_avg)})

    def get_url_pattern(self, url):
        url_patterns = []
        parsed = urlparse(url)
        #print(parsed)
        pattern = parsed.netloc
        p = pattern.split('.')
        pattern = '\.'.join(p)
        pattern = pattern + parsed.path
        return pattern

    def crawl_multiple_article_of_domain(self, domain_url):
        print('crawling domain: ' + domain_url)
        url_list = []
        page = urllib2.urlopen(domain_url)
        page_html = page.read()
        bs = BeautifulSoup(page_html)
        pattern = self.get_url_pattern(domain_url)
        urls = bs.findAll('a', href=re.compile("(" + pattern + ")"))
        if urls is None:
            urls = bs.findAll('a', href=re.compile("(/blogs/)"))

        cnt = 0
        for u in urls:
            if cnt < 10:
                url_list.append(u['href'])
                cnt += 1

        return url_list

    def process_article_details(self, article):
        article_root_paths = []
        content_list = []
        density_list = []
        distance_list = []
        article_root_paths.append(element2path(self.sd.tree, article.root_node))
        content_list.append(article.contents)
        density_list.append(article.density)
        distance_list.append(article.distance_from_root)

        return article_root_paths, content_list, density_list, distance_list

    def process_comment_details(self, comments):
        comment_root_paths = []
        content_list = []
        density_list = []
        distance_list = []

        for comment in comments:
            content_list.append(comment.contents)
            comment_root_paths.append(element2path(self.sd.tree, comment.root_node))#TODO:Save content instead of element to path, but use this for verification
            density_list.append(comment.density)
            distance_list.append(comment.distance_from_root)

        return comment_root_paths, content_list, density_list, distance_list

    def process_multiple_details(self, multiple):
        content_list = []
        density_list = []
        distance_list = []
        multiple_article_root_paths = []
        #print('Inside multiple')
        #print(multiple)
        for article in multiple:
            #print(article.contents, article.root_node, article.density, article.distance_from_root)
            #print(self.sd.tree, article.root_node)
            content_list.append(article.contents)
            multiple_article_root_paths.append(element2path(self.sd.tree, article.root_node))
            density_list.append(article.density)
            distance_list.append(article.distance_from_root)

        return multiple_article_root_paths, content_list, density_list, distance_list


    #def create_blog_domain_url(self, url): #TODO:Test to get the exact domain
    #    url_split = url.split('/')
    #    #while url_split[0] in ['', 'http:', 'https:']:
    #    #    del url_split[0]
    #    print(url_split)
    #    while url_split[len(url_split)-1] == '':
    #        url_split.pop()
    #    page_in_url = url_split.pop()
    #    if len(url_split) <= 3: #This check means, the url and domain are same and there is no sub domain to this url
    #        url_split.append(page_in_url)

    #    domain_to_check = '/'.join(url_split)
    #    self.current_domain = domain_to_check
    #    print('current domain to check' + domain_to_check)
    #    return domain_to_check

    def create_blog_domain_url(self, url):
        domain = ''
        parsed = urlparse(url)
        if parsed.path == '' or parsed.path == '/':
            domain = parsed.scheme + '://' + parsed.netloc
        elif len(parsed.path) > 1:
            path_split = parsed.path.split('/')
            while path_split[len(path_split)-1] == '':
                path_split.pop()
            while path_split[0] == '':
                del(path_split[0])

            if len(path_split) == 1 and 'blog' in str(path_split[0]):
                domain = parsed.netloc + '/' + path_split[0] + '/'
            elif len(path_split) >= 1:
                path_split.pop()
            domain = parsed.scheme + '://' + parsed.netloc + '/' + '/'.join(path_split)

        return domain

    def extract_first_and_last_tags(self, path_lists):
        tag_pairs = {}

        for path_list in path_lists:
            for path in path_list:
                path_split = path.split('/')
                first_tags = ''
                last_tags = ''
                tmp = []
                for tag in path_split:
                    if '[' in tag:
                        t = tag[:tag.index('[')]
                        tmp.append(t)
                    else:
                        tmp.append(tag)
                path_split = tmp

                if len(path_split) > 4:
                    first_tags = path_split[0] + '/' + path_split[1]
                    last_tags = path_split[len(path_split) - 2] + '/' + path_split[len(path_split) - 1]
                #TODO:If pathsplit less than 4 ???
                #TODO:If start tags are /html/body then make changes to code in extraction.py to handle this
                #creating a dictionary with keys as first_tags and values as list of last tags for corresponding first tag
                # the list of last tags contains unique list of tags
                if first_tags in tag_pairs.keys():
                    if last_tags not in tag_pairs[first_tags]:
                        tag_pairs[first_tags].append(last_tags) #TODO:eleminated duplicates
                else:
                    tag_pairs[first_tags] = []
                    tag_pairs[first_tags].append(last_tags)

        return tag_pairs

    def verify_domains(self, domain, details):
        #self.domains_verifiction_result[domain] = ''
        positive_url_details = {}
        verf = Verify()
        verified_result = {}
        print('details: ' + str(details))
        for key in details:
            artcile_type = details[key][0]
            density = details[key][3]
            if len(density) == 0:
                density_avg = 0
            else:
                density_avg = sum(density) / float(len(density))

            if artcile_type == "article":
                verified = verf.verify_article(key, details[key][1])

                if verified:
                    tag_pairs = self.extract_first_and_last_tags(details[key][2])
                    verified_result[key] = [artcile_type, tag_pairs, density_avg]
                    #self.save_best_schema_for_domain(key, artcile_type, tag_pairs)
            elif artcile_type == "comments":
                verified = verf.verify_comments(self.sd.tree, comments=None, root_paths=details[key][1])

                if verified:
                    tag_pairs = self.extract_first_and_last_tags(details[key][2])
                    verified_result[key] = [artcile_type, tag_pairs, density_avg]
                    #self.save_best_schema_for_domain(key, artcile_type, tag_pairs)

            elif artcile_type == "multiple":
                verified = verf.verify_multiple_articles_pagetags_structure(details[key][1])
                if verified:
                    #positive_url_details[key] = [artcile_type, details[key][1]]
                    tag_pairs = self.extract_first_and_last_tags(details[key][2])
                    verified_result[key] = [artcile_type, tag_pairs, density_avg]
                    #self.save_best_schema_for_domain(key, artcile_type, tag_pairs)

        return verified_result

    def process_domains(self, urlstr):
        details = {}

        self.current_domain = self.create_blog_domain_url(urlstr)
        url_list = self.crawl_multiple_article_of_domain(self.current_domain)
        print(url_list)
        for url in url_list:#[0:3]:
            print('url: ' + url)
            self.sd = SDAlgorithm()
            self.sd.url = url
            vals = self.sd.analyze_page()
            #print(self.sd.tree)
            print('vals:')
            print(vals)
            if vals[0] == "article":
                if vals[1] is not None:
                    root_path, contents, density, distance = self.process_article_details(vals[1])
                    details[url] = ["article", root_path, contents, density, distance]
            elif vals[0] == "comment":
                if vals[1] is not None:
                    root_path, contents, density, distance = self.process_article_details(vals[1])
                    details[url] = ["article", root_path, contents, density, distance]
                if len(vals[2]) > 0:
                    root_path, contents, density, distance = self.process_comment_details(vals[2])
                    details[url] = ["comments", root_path, contents, density, distance]
            elif vals[0] == "multiple":
                if len(vals[3]) > 0:
                    root_path, contents, density, distance = self.process_multiple_details(vals[3])
                    details[url] = ["multiple", root_path, contents, density, distance]

            result = self.verify_domains(self.current_domain, details)
            self.save_domain_verification_result(result)


if __name__ == "__main__":
    crawl = CrawlImproperDomains()
    crawl.process_domains('http://www.nike.com/us')