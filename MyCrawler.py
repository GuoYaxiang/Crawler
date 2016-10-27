# -*-coding:utf-8-*-
from bs4 import BeautifulSoup
import socket
import urllib.request
import re
import zlib
from optparse import OptionParser
import logging,doctest


class MyCrawler:
    def __init__(self,seeds):
        #初始化当前抓取的深度
        self.current_deepth = 1
        #利用种子初始化url队列
        self.linkQueue = linkQueue()
        if isinstance(seeds,str):
            self.linkQueue.addUnvisitedUrl(seeds)
        if isinstance(seeds,list):
            for i in seeds:
                self.linkQueue.addUnvisitedUrl(i)
        print("Add the seeds url '%s' to the unvisited url list" % str(self.linkQueue.unvisited))
        
    #抓取过程函数
    def crawling(self,seeds,crawl_deepth):
        #抓取深度不超过crawl_deepth
        while self.current_deepth <= crawl_deepth:
            links = []            
            while self.linkQueue.unvisited:
                #队头出列
                visitUrl = self.linkQueue.unVisitedUrlDequeue()
                print("Pop out one url '%s' from unvisited url list" % visitUrl)
                if visitUrl is None or visitUrl=="":
                    continue
                
                #获取超链接
                links.extend(self.getHyperLinks(visitUrl))
                print("Get %d new links" % len(links))
                
                #将url放入已访问的url中
                self.linkQueue.addVisitedUrl(visitUrl)
                print("Visited url count: "+str(self.linkQueue.getVisitedUrlCount()))
                print("Visited deepth: "+str(self.current_deepth))
                
            #未访问的url入列
            for link in links:
                self.linkQueue.addUnvisitedUrl(link)
            print("%d unvisted links:" % len(self.linkQueue.getUnvisitedUrl()))
            self.current_deepth += 1
    
    
    def getHyperLinks(self,url):
        links = []
        data = self.getPageSource(url)
        if data[0] == "200":
            soup = BeautifulSoup(data[1],"lxml")
            a = soup.findAll("a",{"href":re.compile("^http|^/")})
            for i in a:
                if i["href"].find("http://") != -1:
                    links.append(i["href"])
        return links
    
    #获取网页源码
    def getPageSource(self,url,timeout=10,coding=None):
        try:
            socket.setdefaulttimeout(timeout)
            req = urllib.request.Request(url)
            req.add_header('User-agent','Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')
            resp = urllib.request.urlopen(req)
            page =resp.read()
            if resp.headers.get('Content-Encoding') == 'gzip':
                page = zlib.decompress(page, 16+zlib.MAX_WBITS)
            return ["200",page]
        except Exception as e:
            print(str(e))
            return [str(e),None]
        
        

                
class linkQueue:
    def __init__(self):
        self.visited = []
        self.unvisited = []
          
    def getVisitedUrl(self):
        return self.visited
    
    def getUnvisitedUrl(self):
        return self.unvisited
    
    def addVisitedUrl(self,url):
        self.visited.append(url)
        
    def removeVisitedUrl(self,url):
        self.visited.remove(url)
        
    def unVisitedUrlDequeue(self):
        try:
            return self.unvisited.pop()
        except:
            return None
        
    def addUnvisitedUrl(self,url):
        if url != "" and url not in self.visited and url not in self.unvisited:
            self.unvisited.insert(0,url)
            
    def getVisitedUrlCount(self):
        return len(self.visited)
    
    def getUnvisitedUrlCount(self):
        return len(self.unvisited) == 0
    
    
def main():
    uasge = "usage: %prog [options] arg"
    parser = OptionParser(uasge)
    parser.add_option("-u","--url",action = "store",dest = "UrlSeed",help = "Specify the origin url of the crawler")
    parser.add_option("-d","--depth",action = "store",type = "int",dest = "CrawlDepth",help = "Specify the depth of the crawler",default = 2)
    parser.add_option("-f","--logfile",action = "store",dest = "LogFile",help = "Specify the logfile of the crawler",default = "spider.log")
    parser.add_option("--thread",action = "store",type = "int",dest = "ThreadPool",help = "Specify the size of the threadpool",default = 10)
    parser.add_option("--key",action = "store",dest = "KeyWord",help = "Specify the keyword of the crawler",default = "html")
    parser.add_option("--dbfile",action = "store",dest = "DatabaseFile",help = "Specify the database file of the crawler",default = "spider.db")
    parser.add_option("-l","--level",action = "store",type = "int",dest = "LogLevel",help = "Specify the level of the logging file",default = 2)
    parser.add_option("--testself",action = "store_true",dest = "TestSelf",help = "testself")
    
    
    #解析参数
    [options, args] = parser.parse_args()
    
    if options.TestSelf:      #调用testself函数进行测试，全部采用默认值
        testself()    
        
        
    url_seed = options.UrlSeed
    crawl_depth = options.CrawlDepth
    log_file = options.LogFile
    thread_pool = options.ThreadPool
    key_word = options.KeyWord
    database_file = options.DatabaseFile
    log_level = options.LogLevel
    
    
    #logging模块配置
    logging.basicConfig(filename = log_file, level = log_level)
    
    
    crawl = MyCrawler(url_seed)
    crawl.crawling(url_seed,crawl_depth)
    
    
if __name__ == '__main__':
    #main(["http://www.baidu.com", "http://www.google.com", "http://www.sina.com.cn"],3)
    main()
        