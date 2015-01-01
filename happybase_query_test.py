__author__ = 'freak'
import happybase
import ast

connection = happybase.Connection(host='127.0.0.1', port=9090)
domains_table = connection.table('content')
rows = domains_table.scan()
urlstr = 'http://blog.trove.com/post/87305627825'
articletype = 'article'
verifiedas = 'proper'
paths = "['/html/body/div[3]/div[1]/div[2]/div[2]/div/div[1]/div/div[1]/div[1]/div[1]/div/div[8]', '/html/body/div[3]/div[1]/div[2]/div[1]/div/div[7]/div/ul/li[5]']"
row_count = sum(1 for _ in rows)
rowkey = 'r' + str(row_count + 1)
#domains_table.put(rowkey, {'url:urlttested': urlstr, 'article:type': articletype, 'article:paths': paths, 'verifiedas:v':verifiedas})
#rows = []
rows = domains_table.scan()
#for r in rows1:
#    rows.append(r)
#del(rows[0])

for r in rows:
    #if 'http://www.zeit.de/sport/index' in r[1]['domain:domaintested']:
    if 'http://www.sportsgrid.com/' in r[1]['url:urlstr']:
    #print(r[1]['article:schema'])
        print(r[1])
        #pass
    #tagpairs = str(r[1]['article:schema'])
    #tagpairs = ast.literal_eval(tagpairs)

    #for key in tagpairs.keys():
    #    if 'html' in key:
    #        starttag = '/html/body'
    #    else:
    #        starttag = '/html/body' + key

    #    endtags = tagpairs[key]
    #    for tag in endtags:
    #        print(starttag +'//'+ tag)

a = []
print('\n'.join(a))