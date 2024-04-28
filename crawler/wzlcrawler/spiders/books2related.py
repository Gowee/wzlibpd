import json
import logging
import pathlib

import scrapy
from scrapy.http import Request

BOOKS_PATH = pathlib.Path(__file__).parent / "books2.json" 

logger = logging.getLogger(__name__)


class Books2RelatedSpider(scrapy.Spider):
    name = "books2related"
    allowed_domains = ["wzlib.cn"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "FEEDS": {
            "books2related.json": {
                "format": "jsonl",
                "encoding": "utf8",
                "overwrite": False,
                "store_empty": False,
            },
        },
    }

    def start_requests(self):
        with open(BOOKS_PATH, "r") as f:
            for line in f:
                book = json.loads(line)
                yield request_related(book['Data']['_id'])

    def parse(self, response):
        id = response.meta["id"]
        logger.info(f"id: {id}")
        d = json.loads(response.text)
        yield {"id": id, "related": d}


def request_related(id):
    return Request(
        f"https://oyjy.wzlib.cn/api/search/v1/resource_related/{id}",
        meta={"id": id},
    )
