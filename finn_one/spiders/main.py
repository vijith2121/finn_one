import scrapy
# from finn_one.items import Product
from lxml import html

class Finn_oneSpider(scrapy.Spider):
    name = "finn_one"
    start_urls = ["https://example.com"]

    def parse(self, response):
        parser = html.fromstring(response.text)
        print("Visited:", response.url)
