from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class LawListItem:
    id: str
    title: str
    released_by: str
    publication_date: str
    in_effect_date: str
    type: str
    type_code: int

    @property
    def short_title(self) -> str:
        return self.title.replace("中华人民共和国", "")


@dataclass
class FetchedLawResponse:
    total: int
    items: List[LawListItem]


@dataclass
class FetchedDocumentResponse:
    law_id: str
    path_to_file: Path | None
