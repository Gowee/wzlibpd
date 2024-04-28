#!/usr/bin/env python3
# 20240322 16:07 21519
from _gen import *

DATA_PATH = Path(__file__).parent / "../crawler/wzlcrawler/spiders/books1all.json"


def main():
    by_pdf_url = {}
    books = []
    with open(DATA_PATH) as f:
        for line in f:
            line = json.loads(line)

            if line["SiteTitle"] == "PDF库":
                continue
            elif line["SiteTitle"] == "现代地方文献":
                if re.search("（[唐宋元明清]）", line["author"]) or re.search(
                    "(1[89]([0-6][0-9]|[7][0-4]))|(民国[一二三四五六七八九]年)|(民国[一二三四五]?十)|(民国廿)|(民国六十[一二三])",
                    line["publish_time"],
                ):
                    pass
                else:
                    continue

            line["ATTRS"] = None
            attr_data = json.loads(line["AttrData"])
            if attr_data:
                attr_map = {
                    field["ID"]: (field["Key"] if field["Key"] else field["Title"])
                    for field in line["Fields"]
                }
                line["ATTRS"] = {
                    zhhant(attr_map.get(int(k), k)): zhhant(v)
                    for k, v in attr_data.items()
                }
                for k in itertools.chain(
                    line["ATTRS"],
                    ("author", "publish_time", "publish_house", "isbn", "SiteTitle"),
                ):
                    if not line["ATTRS"].get(k):
                        line["ATTRS"][k] = zhhant(line.get(k))

            if line["pdf_url"] or line["DigitalResourceData"]:
                books.append(line)

            assert not (line["pdf_url"] and line["DigitalResourceData"]), book
            if line["pdf_url"]:
                # assert line['pdf_url'] not in by_pdf_url, line['pdf_url']
                by_pdf_url[line["pdf_url"]] = line

        # index = [line for l in f if (line := json.loads(l))['pdf_url'] or line['DigitalResourceData']]
    # logger.info(f"Count: {len(index)}")
    # by_pdf_url = {e['pdf_url']: e for e in index if e['pdf_url']}

    uploads = []
    indices = [[]]
    counts = [0]
    built_categories = set()

    subs = set()
    for book in books:
        if book["DigitalResourceData"]:
            bookname = zhhant(book["Title"])
            base_categories = set(categorize(sanitize_title(bookname)))

            if len(indices[-1]) >= 10000:
                indices.append([])
                counts.append(0)
            indices[-1].append(
                f"* {bookname}[https://db.wzlib.cn/detail.html?id={book['ID']}]"
            )

            vols = []
            for sub in book["DigitalResourceData"]:
                subs.add(sub["Url"])
                vol = by_pdf_url[sub["Url"]]
                assert vol["Title"] == sub["Title"], f"{vol} {sub}"
                title = sanitize_title(zhhant(vol["Title"]))
                filename = f"WZLib-DB-{vol['ID']} {title}.pdf"
                vols.append((filename, vol))
            prev_filename, last_vol = None, None
            # book_attr_fields =
            for i in range(len(vols)):
                filename, vol = vols[i]
                next_filename, next_vol = (
                    vols[i + 1] if i + 1 < len(vols) else (None, None)
                )

                indices[-1].append(
                    f"** [[:File:{filename}]][https://db.wzlib.cn/detail.html?id={vol['ID']}]"
                )
                counts[-1] += 1

                attrs = book["ATTRS"] or {}
                for k, v in (vol["ATTRS"] or {}).items():
                    if not attrs.get(k):
                        attrs[k] = v
                # assert book['ATTRS'] == vol['ATTRS'], vol['ATTRS']

                attr_fields = "\n".join(
                    [f"  |attr-{k}={v or ''}" for k, v in attrs.items()]
                )
                volname = zhhant(vol["Title"])
                categories = sorted(
                    base_categories | set(categorize(sanitize_title(volname)))
                )

                wikitext = f"""=={{{{int:filedesc}}}}==
{{{{WZLibDBBookNaviBar|prev={prev_filename or ""}|next={next_filename or ""}|nth={i+1}|total={len(vols)}|bookname={bookname}}}}}
{{{{Book in the Wenzhou Library DB
  |id={vol['ID']}
  |title={volname}
  |bookid={book['ID']}
  |booktitle={bookname}
{attr_fields}
}}}}

""" + "".join(
                    f"[[Category:{cat}]]\n" for cat in categories
                )
                url = construct_pdf_url(vol["pdf_url"])
                uploads.append(
                    (
                        "File:" + filename,
                        wikitext,
                        f"{vol['Title']} (batch task; wzlibdb:{vol['ID']}; {i + 1}/{len(vols)} of {bookname}"
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
                            f"{book['Title']} -> {cat} (batch task; wzlibdb:{book['ID']})",
                            None,
                        )
                    )

    for book in books:
        if book["pdf_url"] and book["pdf_url"] not in subs:
            if len(indices[-1]) >= 10000:
                indices.append([])
                counts.append(0)
            title = sanitize_title(zhhant(book["Title"]))
            categories = categorize(title)
            filename = f"WZLib-DB-{book['ID']} {title}.pdf"
            indices[-1].append(
                f"* [[:File:{filename}]][https://db.wzlib.cn/detail.html?id={book['ID']}]"
            )
            counts[-1] += 1
            attr_fields = "\n".join(
                [f"  |attr-{k}={v or ''}" for k, v in (book["ATTRS"] or {}).items()]
            )
            bookname = zhhant(book["Title"])

            wikitext = f"""=={{{{int:filedesc}}}}==
{{{{Book in the Wenzhou Library DB
  |id={book['ID']}
  |title={bookname}
{attr_fields}
}}}}

""" + "".join(
                f"[[Category:{cat}]]\n" for cat in categories
            )
            url = construct_pdf_url(book["pdf_url"])
            uploads.append(
                (
                    "File:" + filename,
                    wikitext,
                    f"{book['Title']} (batch task; wzlibdb:{book['ID']}"
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
                        f"{book['Title']} -> {cat} (batch task; wzlibdb:{book['ID']})",
                        None,
                    )
                )

    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    with open(
        timestamp + ".tsv",
        "w",
    ) as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerows(uploads)

    with open(
        timestamp + ".index.tsv",
        "w",
    ) as f:
        if len(indices) > 1:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            for i in range(len(indices)):
                w.writerow(
                    [
                        f"Commons:Library_back_up_project/file_list/WZLib-DB/{i+1:02}",
                        "\n".join(indices[i]) + "\n",
                        f"Count: {counts[i]}/{sum(counts)}",
                        None,
                    ]
                )
        else:
            f.write('Commons:Library_back_up_project/file_list/WZLib-DB\t"')
            f.writelines(map(lambda line: line + "\n", indices[0]))
            f.write(f'"\tCount: {counts[-1]}\t')

    logger.info(f'Written {timestamp + ".tsv"}, {timestamp + ".index.tsv"}')


if __name__ == "__main__":
    main()
