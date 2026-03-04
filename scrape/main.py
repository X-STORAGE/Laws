import sys
from providers import NationalLawDatabaseProvider, Provider
import re
from model.law import LawListItem
from docx import Document
# from parsers.html import HTMLParser
from parsers.word import WordParser
from parsers.content import ContentParser
from pathlib import Path
import tqdm
import sys


def should_ignore(name) -> bool:
    title = name.replace("中华人民共和国", "")
    if re.search(r"的(决定|复函|批复|答复|批复)$", title):
        return True
    return False


def process_item(provider: Provider, item: LawListItem):
    response = provider.fetch_document(item.id)
    if not response or not response.path_to_file:
        raise ValueError(f"无法获取文件: {item.title}")
    with open(response.path_to_file, "rb") as f:
        document = Document(f)
    parser = WordParser()

    _, desc, content = parser.parse_document(document, item.title)
    filedata = ContentParser().parse(item.title, desc, content)
    if not filedata:
        return

    filename = item.title.replace("中华人民共和国", "")
    if item.publication_date:
        filename = f"{filename}({item.publication_date})"
    filename = f"{filename}.md"

    ret = Path(".") / item.type / filename

    provider.cache_manager.write_law(ret, filedata)


def search_current_effective_law(title: str):
    print(f"Searching {title}", file=sys.stderr)
    p: Provider = NationalLawDatabaseProvider()
    ret = p.fetch(
        use_high_search=True,
        dataList=[
            ("title", title)
        ]
    )
    for item in ret.items:
        process_item(p, item)


def download_all(**kwargs):
    p: Provider = NationalLawDatabaseProvider()
    page = 1
    bar = tqdm.tqdm(total=0, unit="laws", unit_scale=True)
    while True:
        ret = p.fetch(page_num=page, **kwargs)
        if len(ret.items) <= 0:
            break
        bar.total += len(ret.items)
        for item in ret.items:
            if should_ignore(item.title):
                continue
            bar.set_description(f"Processing: {item.short_title}")
            process_item(p, item)
            bar.update(1)
        page += 1


def main():
    if len(sys.argv) == 2:
        law_name = sys.argv[1]
        search_current_effective_law(law_name)
        return
    
    flfgCodeId = [
        # 102, 110, 120, 130, 140, 150, 160, 170, # 法律
        # 180, # 法律解释
        210,  # 行政法规
        311,320,330,340,350 # 司法解释
    ]

    download_all(
        flfgCodeId=flfgCodeId,
    )


if __name__ == "__main__":
    main()
