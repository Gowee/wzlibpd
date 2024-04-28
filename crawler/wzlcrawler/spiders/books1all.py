import json
import logging

import scrapy
from furl import furl

logger = logging.getLogger(__name__)


class Books1AllSpider(scrapy.Spider):
    name = "books1all"
    allowed_domains = ["wzlib.cn"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "FEEDS": {
            "books1all.json": {
                "format": "jsonl",
                "encoding": "utf8",
                "overwrite": False,
                "store_empty": False,
            },
        },
    }

    def __init__(self, start=1, end=600000, *args, **kwargs):
        self.start = int(start)
        self.end = int(end)

        super().__init__(*args, **kwargs)

    def start_requests(self):
        for n in range(self.start, self.end+1):
            yield scrapy.Request(
                    f"https://db.wzlib.cn/search/juhe_detail/{n}/true?Flag=s",
                    callback=self.parse_book_page,
                )

    def parse_book_page(self, response):
        d = json.loads(response.text)
        yield d

