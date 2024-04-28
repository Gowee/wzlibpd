import json
import logging

import scrapy
from scrapy.http import JsonRequest

logger = logging.getLogger(__name__)


class Books2Spider(scrapy.Spider):
    name = "books2"
    allowed_domains = ["wzlib.cn"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "FEEDS": {
            "books2.json": {
                "format": "jsonl",
                "encoding": "utf8",
                "overwrite": False,
                "store_empty": False,
            },
        },
    }

    def start_requests(self):
        yield page_request(1)

    def parse(self, response):
        page = response.meta["page"]
        logger.info(f"page: {page}")

        d = json.loads(response.text)
        for book in d["List"]:
            id = book["_id"]
            yield response.follow(
                f"https://oyjy.wzlib.cn/api/search/v1/resource/{id}",
                callback=self.parse_book_page,
                meta={"page": page},
            )

        if d["IsLastPage"] == True or not d["List"]:
            return

        yield page_request(page + 1)

    def parse_book_page(self, response):
        d = json.loads(response.text)

        d["__page__"] = response.meta["page"]
        yield d


def page_request(page_no=1):
    return JsonRequest(
        f"https://oyjy.wzlib.cn/api/search/v1/page",
        data={
            "f": "",
            "w": "",
            "s": [],
            "t": ["pdf"],
            "r": "",
            "d": "",
            "a": "",
            "ph": "",
            "pt": "",
            "pst": "",
            "vtt": "",
            "c": [],
            "PageSize": 40,
            "PageNum": page_no,
        },
        meta={"page": page_no},
    )
