import pdb
import sys
from pathlib import Path
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer
from autocompletespider import AutocompleteSpider
from anvisaspider import AnvisaSpider

configure_logging()
runner = CrawlerRunner()

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(AutocompleteSpider)
    yield runner.crawl(AnvisaSpider, search=sys.argv[1])
    reactor.stop()

crawl()
reactor.run() # the script will block here until the last crawl call is finished
