import scrapy
from scrapy.crawler import CrawlerProcess
from unidecode import unidecode


author_links = set()

class QuotesSpider(scrapy.Spider):
    name = "quotes"

    custom_settings = {"FEED_FORMAT": "json",
                       "FEED_URI": "quotes.json",
                       "FEED_EXPORT_INDENT": 4
                       }
    
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com"]

    def parse(self, response):
        quotes = response.xpath("/html//div[@class='quote']")
        for quote in quotes:
            tags = quote.xpath("div[@class='tags']/a/text()").extract()
            text = unidecode(quote.xpath("span[@class='text']/text()").get())

            author = quote.xpath("span/small/text()").get()
            author_link = quote.xpath("span[not(contains(@class, 'text'))]/a/@href").get()
            author_links.add(author_link)
            
            yield {
                "tags": tags,
                "author": author,
                "quote": text,
            }

        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link)


class AuthorsSpider(scrapy.Spider):
    name = "authors"

    custom_settings = {"FEED_FORMAT": "json",
                       "FEED_URI": "authors.json",
                       "FEED_EXPORT_INDENT": 4
                       }
    
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com"]

    def parse(self, response):
        for quote in response.xpath("/html//div[@class='quote']"):
            author_info = {
                "fullname": quote.css("small.author::text").get(),
            }
            author_about = response.urljoin(quote.css("a::attr(href)").get())
            yield scrapy.Request(author_about, callback=self.parse_author_info, meta={"author_info": author_info})

        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link, callback=self.parse)

    def parse_author_info(self, response):
        author_info = response.meta["author_info"]
        author_info.update({
            "born_date": response.css("span.author-born-date::text").get(),
            "born_location": response.css("span.author-born-location::text").get(),
            "description": unidecode(response.css("div.author-description::text").get().strip()),
        })
        yield author_info
       
if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(QuotesSpider)
    process.crawl(AuthorsSpider)
    process.start()
