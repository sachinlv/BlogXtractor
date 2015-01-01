'''
Created on Jan 22, 2014

@author: nonlinear
'''

import io
from lxml import html
from BeautifulSoup import BeautifulSoup
import stringops
import os


STANDARD_REPLACEMENT_STRING = "<<?>>"

def code2tree(code):
    return code2tree_ext(code)
    #doc = html.fromstring(code)
    #return doc.getroottree()

def code2tree_ext(code):
    soup = BeautifulSoup(code)
    #code = code.decode("utf-8")
    #code = unicode(soup.prettify(encoding="UTF-8"))
    code = unicode(soup.renderContents(), errors='ignore')
    f = io.StringIO(code)
    tree = html.parse(f)
    return tree

def element2path(tree,element):
    return tree.getpath(element)

def path2element(tree,path):
    return tree.xpath(path)

def element2parentpath(tree,element):
    parent = element.getparent()
    return element2path(tree,parent)

def path2parentpath(path):
    end = path.rfind('/')
    return path[:end]

def path2ancestorpaths(path,no):
    if no > 0:
        parentpath = path2parentpath(path)
        paths = [parentpath]
        paths.extend(path2ancestorpaths(parentpath, no-1))
        return paths
    else:
        return list()

def tree2textnodeslist(tree,element=None):
    if not element:
        text_nodes = tree.xpath('//body//*[not(self::script)]/text()')
    else:
        element = str(element)
        text_nodes = tree.xpath('//body//'+element+'//text()')
    text_nodes_paths = []
    for text in text_nodes:
        parentpath = element2parentpath(tree,text)
        if 'img' in parentpath:
            parentpath = parentpath[:-4]
        text_nodes_paths.append(parentpath)
        #parentpath = tree.getpath(parent)
        #print(text)
        #print(text_nodes_paths[-1])
    return text_nodes, text_nodes_paths

def tree2imgnodeslist(tree):
    img_nodes = tree.xpath('//body//img')
    img_nodes_paths = []
    img_urls = []
    for img_node in img_nodes:
        img_nodes_paths.append(element2path(tree,img_node))
        img_urls.append(img_node.get("src"))
    return img_urls, img_nodes_paths

def tree2attributevalslist(tree):
    attribute_vals = []
    attr_nodes = tree.xpath('//body//*[not(self::script)]/@*')
    return attr_nodes
    

def getposintextnodeslist(tree,text_nodes_paths,node_path):
    if node_path in text_nodes_paths:
        return text_nodes_paths.index(node_path)
    else:
        # if node_path has no text child, get the first text descendant of node_path's ancestor
        while True:
            close_text_nodes = tree.xpath(node_path+"//text()")
            for close_text_node in close_text_nodes:
                path = element2parentpath(tree, close_text_node)
                if path in text_nodes_paths:
                    return text_nodes_paths.index(path)
            else:
                # switch node_path to the node_path's ancestor
                node_path = path2parentpath(node_path)
        
def parentpath2nodetext(tree,nodepath):
    texts = tree.xpath(nodepath+'/text()')
    if texts != None and len(texts)>0:
        return texts[0].strip()
    else:
        return None
 
def isdescendantorelemtype(nodepath, elemtype):
    if '/'+elemtype+'/' in nodepath:
        return True
    elif nodepath.endswith('/'+elemtype):
        return True
    elif '/'+elemtype+'[' in nodepath:
        return True
    return False
   
def ancestorpath2nodestext(tree,nodepath):
    texts = tree.xpath(nodepath+'//text()')
    if texts != None and len(texts)>0:
        return ''.join(texts)
    else:
        return None

def isancestor(nodepath,ancestorpath):
    if len(ancestorpath) < len(nodepath):
        if ancestorpath in nodepath:
            if nodepath[len(ancestorpath)] == '/':
                return True
    return False
    
def isancestororself(nodepath,ancestorpath):
    if isancestor(nodepath, ancestorpath):
        return True
    elif nodepath == ancestorpath:
        return True
    else:
        return False
    
def getcommonancestor(nodepaths):
    prefix = os.path.commonprefix(nodepaths)
    len_prefix = len(prefix)
    len_nodepaths0 = len(nodepaths[0])
    #if len_prefix < len_nodepaths0 and nodepaths[0][len_prefix] != '/':
    
    # unless prefix == nodepath[0], we want to cut up to the next '/' sign, see prefixes: /html/.../div/ or /html/.../div[
    if len_prefix < len_nodepaths0:
        last_slash_pos = prefix.rfind('/')
        prefix = prefix[:last_slash_pos]
    return prefix

def getnameandid(node):
    id = node.get("id")
    name = node.tag
    nameandid = name+"[@id='"+id+"']"
    return nameandid


def template2commonchangingpath(templatepath):
    replstrindex = templatepath.index(STANDARD_REPLACEMENT_STRING)
    commonpathendindex = templatepath.rfind('/',0,replstrindex)
    
    commonpath = templatepath[:commonpathendindex]
    changingpath = templatepath[commonpathendindex:]
    
    print commonpath, changingpath
    
    return commonpath, changingpath


def standardizexpath(tree,nodepath,stoppath=''):
    '''
    standardized xpath is the relative path all of the predecessors with id
    '''
    standardxpathlist = []
    if stoppath == '':
        standardxpathlist.append(nodepath)
    
    parents_w_id = tree.xpath(nodepath+'/ancestor-or-self::*[@id]')
    if parents_w_id != None:
        parents_w_id = reversed(parents_w_id) # start from the deepest one
        
        for parent in parents_w_id:
            parentpath = element2path(tree, parent)
            
            if(isancestororself(stoppath,parentpath)):
                relpath = '//'+getnameandid(parent)+nodepath.replace(parentpath,'')
                standardxpathlist.append(relpath)
            else:
                break
    
    return standardxpathlist


def findcommonstandardxpath(tree,templatepath,nodepaths):
    
    commonpath,changingpath = template2commonchangingpath(templatepath)
    
    standardxpathlist = []
    
    # get paths starting from the common node with id
    commonxpathlist = standardizexpath(tree, commonpath)
    for path in commonxpathlist:
        fullxpath = path+changingpath
        standardxpathlist.append(fullxpath)
    
    # get paths starting from the uncommon nodes with ids and try to find naming rules
    nodesxpathlists = []
    for nodepath in nodepaths:
        nodexpathlist = standardizexpath(tree, nodepath, commonpath)
        nodesxpathlists.append(nodexpathlist)
        
    for j in range(len(nodesxpathlists[0])):
        strings = []
        for i in range(len(nodesxpathlists)):
            strings.append(nodesxpathlists[i][j])
        string_no, common_beg, diff_middle, common_end = stringops.find_difference_inside(strings)
        templatepath = common_beg+STANDARD_REPLACEMENT_STRING+common_end
        standardxpathlist.append(templatepath)
        
    return standardxpathlist 























    
    


