from sd_algorithm import SDAlgorithm
import happybase
from verification import Verify
from extraction import ExtractContent
from domainanalysis import CrawlImproperDomains

global IS_DOM_VERIFIED

class DataImport:
    def __init__(self):
        #self.url = "http://techcrunch.com/"
        self.urls = []
        self.table = None
        self.connection = None

    def database_connect(self):
        self.connection = happybase.Connection(host='127.0.0.1', port=9090)

    def get_urls(self):
        self.table = self.connection.table('urls')
        rows = self.table.scan()

        for r in rows:
            print(r[1].values()[0])
            self.urls.append(r[1].values()[0])
        #print(self.urls)
        return self.urls

    def get_verified_domains(self):
        verified_domains = []
        self.table = self.connection.table('verifieddomains')
        rows = self.table.scan()

        for r in rows:
            verified_domains.append(r[1]['domain:domaintested'])

        return verified_domains

    def get_no_of_urls(self):
        return len(self.urls)


class Classify:
    def __init__(self):
        global IS_DOM_VERIFIED

        db = DataImport()
        db.database_connect()
        urls = db.get_urls()
        #pos_doms, neg_doms = db.get_verified_domains()
        ver_doms = db.get_verified_domains()
        self.verify = Verify()
        self.extr = ExtractContent()
        ver = None
        for url in urls:
            ver = self.verify.verify_url_domain(url, ver_doms)
            IS_DOM_VERIFIED = ver
            self.classify_page(url)

    def classify_page(self, urlstr):
        global IS_DOM_VERIFIED

        export = Export()
        export.database_connect()

        sd = SDAlgorithm()
        sd.url = urlstr
        vals = sd.analyze_page()
        tree = sd.tree
        self.pagetype = ''

        if vals[0] == 'article':
            isarticle = self.verify.verify_article(urlstr, vals[1])

            if isarticle:
                self.extr.extract_article(urlstr)
                export.export_urls(urlstr, 'proper', 'article', vals[1])
            elif not isarticle:
                self.pagetype = self.reclassify('article')
                export.export_urls(urlstr, 'improper', 'article', vals[1])

                if IS_DOM_VERIFIED is not None:
                    if IS_DOM_VERIFIED:
                        self.extr.extract_with_best_schema(urlstr, self.pagetype)
                    elif not IS_DOM_VERIFIED:
                        crawl = CrawlImproperDomains()
                        crawl.process_domains(urlstr)
                        self.extr.extract_with_best_schema(urlstr, self.pagetype)


        elif vals[0] == 'comment':
            isarticle = self.verify.verify_article(urlstr, vals[1])
            iscomments = self.verify.verify_comments(tree, comments=vals[2])

            if isarticle and iscomments:
                self.extr.extract_article(urlstr)
                self.extr.extract_comment(vals[2], urlstr)
                export.export_urls(urlstr, 'proper', 'comment', vals[1], vals[2])
            else:
                self.pagetype = self.reclassify('comment')
                export.export_urls(urlstr, 'improper', 'comment', vals[1], vals[2])

                if IS_DOM_VERIFIED is not None:
                    if not IS_DOM_VERIFIED:
                        crawl = CrawlImproperDomains()
                        crawl.process_domains(urlstr)
                    self.extr.extract_with_best_schema(urlstr, self.pagetype)

        elif vals[0] == 'multiple':
            ismultiple = self.verify.verify_multiple_articles(vals[3], urlstr, tree)

            if ismultiple:
                self.extr.extract_multiple_article(vals[3], urlstr)
                export.export_urls(urlstr, 'proper', 'multiple', None, vals[3])
            else:
                self.pagetype = self.reclassify('multiple')
                export.export_urls(urlstr, 'improper', 'multiple', None, vals[3])

                if IS_DOM_VERIFIED is not None:
                    if not IS_DOM_VERIFIED:
                        crawl = CrawlImproperDomains()
                        crawl.process_domains(urlstr)
                    self.extr.extract_with_best_schema(urlstr, self.pagetype)

    def reclassify(self, currentType):
        classified_type = ''
        if currentType == 'article':
            classified_type = 'article' #TODO: find the right alternative
        if currentType == 'comment':
            classified_type = 'multiple'
        elif currentType == 'multiple':
            classified_type = 'article'

        return classified_type


class Export:
    def __init__(self):
        self.table = None

    def database_connect(self):
        connection = happybase.Connection(host='127.0.0.1', port=9090)
        self.table = connection.table('urlstested')

    def get_next_rowid(self):
        rows = self.table.scan()
        row_count = sum(1 for _ in rows)
        rowkey = 'r' + str(row_count + 1)
        return rowkey

    def export_urls(self, urlstr, verf_type, article_type,  article_tag_struct, other_tag_struct = None):
        #calculate the next row key
        if article_tag_struct is not None:
            self.table.put(self.get_next_rowid(), {'url:urlttested': urlstr, 'article:type': article_type, 'article:paths': str(article_tag_struct.contents), 'verifiedas:v': verf_type})

        if other_tag_struct is not None:
            paths = []
            for o in other_tag_struct:
                paths.append(o.contents)

            self.table.put(self.get_next_rowid(), {'url:urlttested': urlstr, 'article:type': article_type, 'article:paths': str(paths), 'verifiedas:v': verf_type})


if __name__ == "__main__":
    classify = Classify()