import json
import logging

import scrapy
from furl import furl

logger = logging.getLogger(__name__)


class Books1Spider(scrapy.Spider):
    name = "books1"
    allowed_domains = ["wzlib.cn"]
    start_urls = [
        "https://db.wzlib.cn/search/juhe_item_l/91?Flag=s&TypeTag=13&Ids=35,31,38,86,93,91,52,84,18,32,23,17,87,29,15,26,19,27,85,82,81,83,25,39&Selected=&PageNum=1&PageSize=50"
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "FEEDS": {
            "books1.json": {
                "format": "jsonl",
                "encoding": "utf8",
                "overwrite": False,
                "store_empty": False,
            },
        },
    }

    def parse(self, response):
        url = furl(response.url)
        page = int(url.args["PageNum"])

        d = json.loads(response.text)
        for book in d["List"]:
            id = book["ID"]
            yield response.follow(
                f"https://db.wzlib.cn/search/juhe_detail/{id}/true?Flag=s",
                callback=self.parse_book_page,
                meta={"page": page},
            )

        if d.get("IsLastPage") == True or not d.get("List"):
            return

        url.args["PageNum"] = page + 1
        yield response.follow(url.url, callback=self.parse)

    def parse_book_page(self, response):
        d = json.loads(response.text)

        d["__page__"] = response.meta["page"]
        yield d

        # id = d['ID']
        # title = d['Title']
        # catid = d['SiteID']
        # catname = d['SiteTitle']

        # cover_url = furl(response.url).join(d['pic_url']).url
        # pdf_url = furl(response.url).join(d['pdf_url'])
        # if pdf_url.path == "/digital_resource/web/viewer.html":
        #     pdf_url.join(pdf_url.args['file'])

        # yield {
        #     'id': id,
        #     'title': title,
        #     'catid': catid,
        #     'catname': catname,

        # }
