import sys
from pathlib import Path
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer
from anvisautocompletespider import AnvisaAutocompleteSpider
from anvisabulariospider import AnvisaBularioSpider

configure_logging()
runner = CrawlerRunner()

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(AnvisaAutocompleteSpider)
    yield runner.crawl(AnvisaBularioSpider, search=sys.argv[1])
    reactor.stop()

if len(sys.argv) >= 2:
    crawl()
    reactor.run() # the script will block here until the last crawl call is finished
else:
    raise Exception('Indique o parametro de busca do medicamento')