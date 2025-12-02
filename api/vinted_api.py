import requests
import logging
import json
from typing import Dict, List

logger = logging.getLogger(__name__)


class VintedAPI:
    def __init__(self, country_code=".fr", cookies_file="cookies.json"):
        self.session = requests.Session()
        self.country_code = country_code
        self.base_url = f"https://www.vinted{country_code}"
        self.cookies_file = cookies_file

        # Carica automaticamente i cookie
        self.load_cookies()

    # -----------------------------
    #  CARICA COOKIE DI TIPO DICT
    # -----------------------------
    def load_cookies(self):
        try:
            with open(self.cookies_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            # Se è una lista → vecchio formato: [{name:"", value:""}, ...]
            if isinstance(cookies, list):
                for cookie in cookies:
                    self.session.cookies.set(cookie["name"], cookie["value"])

            # Se è un dict → nuovo formato: {"cf_clearance":"...", ...}
            elif isinstance(cookies, dict):
                for name, value in cookies.items():
                    self.session.cookies.set(name, value)

            logger.info("🍪 Cookies caricati correttamente.")

        except Exception as e:
            logger.error(f"❌ Errore nel caricamento dei cookie: {e}")

    # -----------------------------
    #        HEADERS REALI
    # -----------------------------
    def _get_headers(self) -> Dict:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9",
            "Referer": f"https://www.vinted{self.country_code}/",
            "X-Requested-With": "XMLHttpRequest",
            # Importantissimo: usa i cookie per evitare 401
            "Authorization": f"Bearer {self.session.cookies.get('access_token_web', '')}"
        }

    # -----------------------------
    #       FUNZIONE DI RICERCA
    # -----------------------------
    async def search_products(self, search_text: str) -> List[Dict]:
        try:
            params = {
                "page": 1,
                "per_page": 20,
                "search_text": search_text,
                "order": "newest_first",
                "currency": "EUR",
                "is_for_sale": "1",
                "catalog_ids": "",
            }

            response = self.session.get(
                f"{self.base_url}/api/v2/catalog/items",
                params=params,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 401:
                logger.error("❌ 401 Unauthorized → Cookie/token scaduti.")
                return []

            if response.status_code == 403:
                logger.error("❌ 403 Forbidden → Vinted ha bloccato la richiesta.")
                return []

            response.raise_for_status()
            data = response.json()

            items = []
            for item in data.get("items", []):
                photos = item.get("photos", [])
                item["image_url"] = photos[0]["url"] if photos else None
                items.append(item)

            return items

        except Exception as e:
            logger.error(f"❌ Errore nella ricerca prodotti: {e}")
            return []
