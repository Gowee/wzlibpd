#!/usr/bin/env python3
# 20240322 16:07 21519
from _gen import *
import _gen

BOOKS_PATH = Path(__file__).parent / "../crawler/wzlcrawler/spiders/books2.json"
RELATED_PATH = (
    Path(__file__).parent / "../crawler/wzlcrawler/spiders/books2related.json"
)
TAG = "wzliboyjy"


def genattrs(book):
    return {
        k: zhhant(v) if isinstance(v, (str, type(None))) else v["url"]
        for k, v in book.items()
        if k.startswith("wzl")
    }


def genattrfields(attrs):
    return "\n".join([f"  |attr-{k}={v or ''}" for k, v in attrs.items()])


def genprefix(book):
    return f"WZLib-OYJY-{book['_id']}"  # for simplicity and consistency, for now
    # if gjid := book.get("wzl_gj_id"):
    #     prefix = f"WZLib-{gjid}"
    # else:
    #     prefix = f"WZLib-OYJY-{book['_id']}"
    # return prefix


def sanitize_title(title):
    title = title.replace(
        "尚志堂詩稿七卷仰止集一卷仰止集之餘一卷臥遊百詠一卷還珠亭日課編二卷篔林詩鈔不分卷",
        "尚志堂詩稿、仰止集、仰止集之餘、臥遊百詠、還珠亭日課編、篔林詩鈔",
    )
    return _gen.sanitize_title(title)


def categorize(title):
    cats = _gen.categorize(title)
    try:
        cats.remove("尚志堂詩稿、仰止")
    except ValueError:
        pass
    return cats


def main():
    by_pdf_url = {}
    books = {}
    with open(BOOKS_PATH) as f:
        for line in f:
            line = json.loads(line)

            if line["Srouce"]["Title"] == "现代地方文献":
                if (
                    re.search("（[唐宋元明清]）", line["Data"].get("dc_publisher"))
                    or re.search(
                        "([19]([0-6][0-9]|[7][0-4]))|(民国[一二三四五六七八九]年)|(民国[一二三四五]?十)|(民国廿)|(民国六十[一二三])",
                        line["Data"]["wzl_publication_time"],
                    )
                    or re.search(
                        "(谢灵运|郑振铎|鲁迅)", line["Data"].get("dc_publisher")
                    )
                ):
                    pass
                else:
                    continue
            assert line["Data"]["dc_title"]
            books[line["Data"]["_id"]] = line

    related = {}
    with open(RELATED_PATH) as f:
        for line in f:
            line = json.loads(line)
            base_id = line["id"]
            for rel in line["related"]:
                assert rel["title"] in (
                    "分卷分册",
                    "民国文献（封面图）",
                    "温图古籍-分卷分册",
                ), (
                    "Unknonw relation:" + title
                )
                if "分卷分册" in rel["title"]:
                    assert base_id not in related
                    related[base_id] = rel

    subs = set()

    uploads = []
    indices = [[]]
    counts = [0]
    built_categories = set()

    for book in books.values():
        if rel := related.get(book["Data"]["_id"]):
            assert not book["Data"].get("wzl_gj_id")
            assert not book["Data"].get("wzl_pdf_url")
            assert not book["RelateList"]
            collection = zhhant(book["Srouce"]["Title"])
            book = book["Data"]

            bookname = zhhant(book["dc_title"])
            base_categories = set(categorize(sanitize_title(bookname)))
            bookattrs = genattrs(book)
            book_byline = zhhant(book.get("dc_publisher"))
            book_description = zhhant(book.get("dc_description"))

            if len(indices[-1]) >= 10000:
                indices.append([])
                counts.append(0)
            indices[-1].append(
                f"* {bookname}[https://oyjy.wzlib.cn/detail.html?id={book['_id']}]"
            )

            vols = []
            for vol in rel["items"]:
                subs.add(vol["_id"])
                assert not any(
                    "分卷分册" in rr["title"] for rr in related.get(vol["_id"], {})
                )
                if vol["_id"] in books:
                    # Some items are missing due to unknown reasons, such as 61e4cff7727da20473b3f6a7
                    assert (genattrs(vol) | {"wzl_pdf_url": None}) == (
                        genattrs(books[vol["_id"]]["Data"] | {"wzl_pdf_url": None})
                    ), repr(vol)
                    vol = books[vol["_id"]]["Data"]
                title = sanitize_title(zhhant(vol["dc_title"]))
                filename = f"{genprefix(vol)} {title}.pdf"
                vols.append((filename, vol))
            prev_filename, last_vol = None, None
            # book_attrfields =
            for i in range(len(vols)):
                filename, vol = vols[i]
                assert len(filename.encode("utf-8")) < 240, filename
                next_filename, next_vol = (
                    vols[i + 1] if i + 1 < len(vols) else (None, None)
                )

                indices[-1].append(
                    f"** [[:File:{filename}]][https://oyjy.wzlib.cn/resource/?id={vol['_id']}]"
                )
                counts[-1] += 1

                attrs = genattrs(vol)
                for k, v in bookattrs.items():
                    if not attrs.get(k):
                        attrs[k] = v
                attrfields = genattrfields(attrs)
                volname = zhhant(vol["dc_title"])
                byline = book_byline or zhhant(vol.get("dc_publisher"))
                assert (not book_description) or (not vol.get("dc_description"))
                description = book_description or zhhant(vol.get("dc_description"))
                categories = sorted(
                    base_categories | set(categorize(sanitize_title(volname)))
                )

                wikitext = f"""=={{{{int:filedesc}}}}==
{{{{WZLibOYJYBookNaviBar|prev={prev_filename or ""}|next={next_filename or ""}|nth={i+1}|total={len(vols)}|booktitle={bookname}}}}}
{{{{Book in the Wenzhou Library DB
  |id={vol['_id']}
  |title={volname}
  |byline={byline or ""}
  |description={description or ""}
  |bookid={book['_id']}
  |booktitle={bookname}
  |collection={collection}
{attrfields}
}}}}

""" + "".join(
                    f"[[Category:{cat}]]\n" for cat in categories
                )
                url = construct_pdf_url(vol["wzl_pdf_url"])
                uploads.append(
                    (
                        "File:" + filename,
                        wikitext,
                        f"{vol['dc_title']} (batch task; {TAG}:{vol['_id']}; {i + 1}/{len(vols)} of {bookname}"
                        + (
                            (
                                "; "
                                + ", ".join(
                                    f"[[:c:Category:{cat}|{cat}]]" for cat in categories
                                )
                            )
                            if categories
                            else ""
                        )
                        + ")",
                        url,
                    )
                )
                prev_filename, prev_vol = vols[i]

                for cat in categories:
                    if cat in built_categories:
                        continue
                    built_categories.add(cat)
                    category_wikitext = generate_category_wikitext(cat)
                    uploads.append(
                        (
                            "Category:" + cat,
                            category_wikitext,
                            f"{book['dc_title']} -> {cat} (batch task; {TAG}:{book['_id']})",
                            None,
                        )
                    )

    for book in books.values():
        if book["Data"]["_id"] in subs or not book["Data"].get("wzl_pdf_url"):
            continue
        if len(indices[-1]) >= 10000:
            indices.append([])
            counts.append(0)

        collection = zhhant(book["Srouce"]["Title"])
        book = book["Data"]
        title = sanitize_title(zhhant(book["dc_title"]))
        categories = categorize(title)
        filename = f"{genprefix(book)} {title}.pdf"
        assert len(filename.encode("utf-8")) < 240, filename
        indices[-1].append(
            f"* [[:File:{filename}]][https://oyjy.wzlib.cn/resource/?id={book['_id']}]"
        )
        counts[-1] += 1
        attrs = genattrs(book)
        attrfields = genattrfields(attrs)
        bookname = zhhant(book["dc_title"])
        book_byline = zhhant(book.get("dc_publisher"))
        book_description = zhhant(book.get("dc_description"))

        wikitext = f"""=={{{{int:filedesc}}}}==
{{{{Book in the Wenzhou Library OYJY
  |id={book['_id']}
  |title={bookname}
  |byline={byline or ""}
  |description={description or ""}
  |collection={collection}
{attrfields}
}}}}

""" + "".join(
            f"[[Category:{cat}]]\n" for cat in categories
        )
        url = construct_pdf_url(book["wzl_pdf_url"])
        uploads.append(
            (
                "File:" + filename,
                wikitext,
                f"{book['dc_title']} (batch task; {TAG}:{book['_id']}"
                + (
                    (
                        "; "
                        + ", ".join(
                            f"[[:c:Category:{cat}|{cat}]]" for cat in categories
                        )
                    )
                    if categories
                    else ""
                )
                + ")",
                url,
            )
        )

        for cat in categories:
            if cat in built_categories:
                continue
            built_categories.add(cat)
            category_wikitext = generate_category_wikitext(cat)
            uploads.append(
                (
                    "Category:" + cat,
                    category_wikitext,
                    f"{book['dc_title']} -> {cat} (batch task; {TAG}:{book['_id']})",
                    None,
                )
            )

    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    pages_path = f"{TAG}-pages.{timestamp}.tsv"
    indices_path = f"{TAG}-indices.{timestamp}.tsv"
    with open(
        pages_path,
        "w",
    ) as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerows(uploads)

    with open(
        indices_path,
        "w",
    ) as f:
        if len(indices) > 1:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            for i in range(len(indices)):
                w.writerow(
                    [
                        f"Commons:Library_back_up_project/file_list/WZLib-OYJY/{i+1:02}",
                        "\n".join(indices[i]) + "\n",
                        f"Count: {counts[i]}/{sum(counts)}",
                        None,
                    ]
                )
        else:
            f.write('Commons:Library_back_up_project/file_list/WZLib-OYJY\t"')
            f.writelines(map(lambda line: line + "\n", indices[0]))
            f.write(f'"\tCount: {counts[-1]}\t')

    logger.info(f"Written {sum(counts)} files into {pages_path}, {indices_path}")


if __name__ == "__main__":
    main()
