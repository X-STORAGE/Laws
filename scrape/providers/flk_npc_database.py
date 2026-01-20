import requests
from model.law import FetchedLawResponse, LawListItem, FetchedDocumentResponse
from .base import Provider
from .cache_provider import cache, CacheType


class NationalLawDatabaseProvider(Provider):
    BASE_URL = "https://flk.npc.gov.cn"
    HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://flk.npc.gov.cn",
        "Referer": "https://flk.npc.gov.cn/search",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    }

    def fetch(self, page_num=1, page_size=20, **kwargs) -> FetchedLawResponse:
        response = self.__search(
            page_num=page_num,
            page_size=page_size,
            **kwargs
        )

        rows = response.get("rows", [])

        def map_item(item: dict):
            return LawListItem(
                id=item.get("bbbs", ""),
                title=item.get("title", ""),
                released_by=item.get("zdjgName", ""),
                publication_date=item.get("gbrq", ""),
                in_effect_date=item.get("sxrq", ""),
                type=item.get("flxz", ""),
                type_code=item.get("flfgCodeId", 0),
            )
        return FetchedLawResponse(
            total=response.get("total", 0),
            items=list(map(map_item, rows)),
        )

    def fetch_document(self, law_id: str) -> FetchedDocumentResponse | None:
        full_url = f"{self.BASE_URL}/law-search/download/pc?format=docx&bbbs={law_id}"
        response = requests.get(
            full_url,
            headers=self.HEADERS,
        )
        response.raise_for_status()
        response_data = response.json()
        download_url = response_data.get("data", {}).get("url", "")
        if not download_url:
            return None

        # {"msg": "操作成功", "code": 200, "data": {"urlIn": "http://172.16.220.27:38080/law-search/file/download?filePath=/prod/20251227/5036535b8e084dffb96aebc07a8a7ea3.docx&fileName=中华人民共和国国家通用语言文字法_20251227.docx&response-content-disposition=attachment;filename=\"中华人民共和国国家通用语言文字法_20251227.docx\"",
        #                                       "url": "https://flkoss.obs-bj2.cucloud.cn/prod/20251227/5036535b8e084dffb96aebc07a8a7ea3.docx?response-content-disposition=attachment%3B%20filename%3D%22%25E4%25B8%25AD%25E5%258D%258E%25E4%25BA%25BA%25E6%25B0%2591%25E5%2585%25B1%25E5%2592%258C%25E5%259B%25BD%25E5%259B%25BD%25E5%25AE%25B6%25E9%2580%259A%25E7%2594%25A8%25E8%25AF%25AD%25E8%25A8%2580%25E6%2596%2587%25E5%25AD%2597%25E6%25B3%2595_20251227.docx%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20260106T015131Z&X-Amz-SignedHeaders=host&X-Amz-Expires=3600&X-Amz-Credential=8uue2voatpgnwukhfj46%2F20260106%2Fcn-north-1%2Fs3%2Faws4_request&X-Amz-Signature=f5df9f3e305334b28a074cb32894e8b22201c4e6ee6f1a0cb7cd7e46afc08452"}}

        path = self.cache_manager.download_binary(
            download_url,
            CacheType.WordDocument,
        )
        if path is None:
            return None
        return FetchedDocumentResponse(
            law_id=law_id,
            path_to_file=path,
        )

    @cache(CacheType.WebPage, filetype="json")
    def __search(self, page_num=1, page_size=20, **kwargs) -> dict:
        type_codes = kwargs.get(
            "type_codes",
            [102, 110, 120, 130, 140, 150, 160, 170, 180, 190, 195],
        )
        released_by = kwargs.get("released_by", [])

        payload = {
            "searchRange": 1,
            "sxrq": [],
            "gbrq": [],
            "searchType": 2,
            "sxx": [],
            "gbrqYear": [],
            "flfgCodeId": type_codes,
            "zdjgCodeId": released_by,
            "searchContent": "",
            "orderByParam": {"order": "gbrq", "sort": "DESC"},
            "pageNum": page_num,
            "pageSize": page_size
        }

        response = requests.post(
            self.BASE_URL + "/law-search/search/list",
            headers=self.HEADERS,
            json=payload
        )

        response.raise_for_status()
        return response.json()
