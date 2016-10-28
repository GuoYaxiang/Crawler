# -*-coding:utf-8-*-
from bs4 import BeautifulSoup
import socket
import urllib.request
import re
import gzip
from optparse import OptionParser
import logging,doctest
import queue
import threading,sys,time
import chardet

lock = threading.Lock()
class MyCrawler:
    def __init__(self,seeds,crawl_depth,thread_num):
        #初始化抓取的深度
        self.crawl_depth = crawl_depth
        #利用种子初始化url队列
        self.visited_url = []
        self.threadpool = ThreadPool(thread_num)

        if isinstance(seeds,str):
            self.threadpool.addTask(self.crawling,url = seeds,current_depth = 1)
        if isinstance(seeds,list):
            for i in seeds:
                self.threadpool.addTask(self.crawling,url = i,current_depth = 1)
        print("Add the seeds url '%s' to the unvisited url list" % str(seeds))

    def work(self):
        self.threadpool.waitForComplete()

    #抓取过程函数
    def crawling(self,url,current_depth):
        #抓取深度不超过crawl_depth
        if current_depth <= self.crawl_depth:
            links = []

            #获取超链接
            links.extend(self.getHyperLinks(url))
            print("Get %d new links" % len(links))

            #将url放入已访问的url中
            self.visited_url.append(url)
            print("visited url count: "+str(len(self.visited_url)))
            print("Visited depth: "+str(current_depth))

            #未访问的url入列
            lock.acquire()
            for link in links:
                if (link not in self.visited_url) and (current_depth<self.crawl_depth):
                    length = self.threadpool.addTask(self.crawling,url = link,current_depth = current_depth+1)
            lock.release()


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
                page = gzip.decompress(page)
            
            charset = chardet.detect(page)['encoding']
            print(charset)
            page = page.decode(charset)
            return ["200",page]
        except Exception as e:
            print(str(e))
            return [str(e),None]


class workThread(threading.Thread):
    def __init__(self,task_queue):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.daemon = True
        self.start()
        self.idle = True

    def run(self):
        sleep_time = 0.01
        multiply = 1
        while True:
            try:
                func,args,kwargs = self.task_queue.get(block = False)
                self.idle = False
                multiply = 1

                func(*args,**kwargs)
            except queue.Empty:
                time.sleep(sleep_time*multiply)
                self.idle = True
                multiply *= 2
                continue
            except:
                print(sys.exc_info())
                raise

class ThreadPool:
    def __init__(self,thread_num,max_queue_len = 1000):
        self.max_queue_len = max_queue_len
        self.task_queue = queue.Queue(max_queue_len)
        self.threads = []
        self.__createPool(thread_num)

    def __createPool(self,thread_num):
        for i in range(thread_num):
            thread = workThread(self.task_queue)
            self.threads.append(thread)

    def addTask(self,func,*args,**kwargs):
        '''
           添加一个任务，返回任务等待队列的长度
        '''
        try:
            self.task_queue.put((func,args,kwargs))
        except queue.Full:
            raise   #队列已满，抛出异常
        return self.task_queue.qsize()

    def waitForComplete(self):
        while not self.task_queue.empty():
            time.sleep(2)

        while True:
            all_idle = True
            for th in self.threads:
                if not th.idle:
                    all_idle = False
                    break
            if all_idle:
                break
            else:
                time.sleep(1)


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
    thread_num = options.ThreadPool
    key_word = options.KeyWord
    database_file = options.DatabaseFile
    log_level = options.LogLevel


    #logging模块配置
    logging.basicConfig(filename = log_file, level = log_level)


    crawl = MyCrawler(url_seed,crawl_depth,thread_num)
    crawl.work()
    #crawl.crawling(url_seed,crawl_depth)


if __name__ == '__main__':
    #main(["http://www.baidu.com", "http://www.google.com", "http://www.sina.com.cn"],3)
    main()

