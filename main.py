from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests
import json
import re
import time
import random


class TokopediaShopScraper:
    def __init__(self, shop_domain):
        self.shop_domain = shop_domain
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": UserAgent().random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
        })
        self.data = {}
        self.root = {}

    def fetch_apollo_state(self, max_retries=5):
        url = f"https://www.tokopedia.com/{self.shop_domain}"
    
        for attempt in range(1, max_retries + 1):
            try:
                self.session.headers["User-Agent"] = UserAgent().random
                time.sleep(random.uniform(2, 4))
                response = self.session.get(url, timeout=30)
    
                if response.status_code != 200 or "window.__APOLLO_STATE__" not in response.text:
                    print(f"[Attempt {attempt}] Gagal: status={response.status_code}, konten tidak valid")
                    continue
    
                soup = BeautifulSoup(response.text, "html.parser")
                script_tag = soup.find("script", string=lambda t: t and "window.__APOLLO_STATE__" in t)
                if not script_tag:
                    print(f"[Attempt {attempt}] Script __APOLLO_STATE__ tidak ditemukan.")
                    continue
    
                pattern = re.compile(r"window\.__APOLLO_STATE__\s*=\s*({.*});?", re.DOTALL)
                match = pattern.search(script_tag.string or script_tag.text)
                if not match:
                    print(f"[Attempt {attempt}] Regex gagal mengekstrak JSON.")
                    continue
    
                self.data = json.loads(match.group(1))
                self.root = self.data["ROOT_QUERY"]
                print(f"[Success] Data berhasil diambil pada percobaan ke-{attempt}")
                return
    
            except Exception as e:
                print(f"[Attempt {attempt}] Error: {e}")
    
        raise ValueError("Gagal mengambil data Apollo State setelah beberapa percobaan.")

    def get_shop_info(self):
        shop_key = next(k for k in self.root if k.startswith("shopInfoByID"))
        shop_ref = self.root[shop_key]["result"][0]["__ref"]
        shop_data = self.data[shop_ref]

        core = shop_data["shopCore"]
        status = self.data[shop_data["statusInfo"]["__ref"]]
        gold = self.data[shop_data["goldOS"]["__ref"]]
        favorite = self.data[shop_data["favoriteData"]["__ref"]]
        location = self.data[shop_data["shippingLoc"]["__ref"]]
        create = shop_data["createInfo"]
        shipments = [self.data[ref["__ref"]]["name"] for ref in shop_data["shipmentInfo"]]

        return {
            "id": core["shopID"],
            "name": core["name"],
            "location": f"{location['districtName']}, {location['cityName']}",
            "is_verified": status["shopStatus"] == 1,
            "is_gold_merchant": gold["isGold"] == 1,
            "favorites": favorite["totalFavorite"],
            "created_at": create["shopCreated"],
            "shipments": shipments
        }

    def get_shop_performance(self):
        layout_key = next(k for k in self.root if k.startswith("ShopPageGetHeaderLayout"))
        widgets = self.root[layout_key]["widgets"]

        operational, handling = None, None
        for widget in widgets:
            if widget["name"] == "shop_performance":
                for comp in widget["component"]:
                    if comp["name"] == "shop_operational_hour":
                        operational = comp["data"]["text"][0]["textHtml"]
                    elif comp["name"] == "shop_handling":
                        handling = comp["data"]["text"][0]["textHtml"]

        return {
            "operational_hour": operational,
            "handling_time": handling
        }

    def get_rating_data(self):
        rating_key = next(k for k in self.root if k.startswith("productrevGetShopRating"))
        rating_data = self.root[rating_key]

        distribution = {
            item["rate"]: item["totalReviews"]
            for item in rating_data["detail"]
        }

        return {
            "average_rating": rating_data["ratingScore"],
            "total_reviews": rating_data["totalRating"],
            "rating_distribution": distribution
        }

    def get_products(self):
        total_sold = 0
        product_list = []
    
        product_key = next((k for k in self.root if k.startswith("GetShopProduct")), None)
        if product_key and "data" in self.root[product_key]:
            product_data = self.root[product_key]
            for item_ref in product_data["data"]:
                item = self.data[item_ref["__ref"]]
                stats = item.get("stats", {})
                product_list.append({
                    "name": item["name"],
                    "stock": item["stock"],
                    "sold": item["sold"],
                    "rating": stats.get("rating", 0),
                    "review_count": stats.get("reviewCount", 0),
                    "average_rating": stats.get("averageRating", "0")
                })
                total_sold += item["sold"]
    
            return {
                "total_products": product_data["totalData"],
                "total_sold": total_sold,
                "products": product_list
            }
    
        layout_key = next((k for k in self.root if k.startswith("shopPageGetLayoutV2")), None)
        if layout_key:
            widgets = self.root[layout_key].get("widgets", [])
            for widget in widgets:
                if widget.get("name") == "product" and "data" in widget:
                    for prod in widget["data"]:
                        if prod.get("__typename") == "ProductWidget":
                            product_list.append({
                                "name": prod.get("name"),
                                "stock": None,
                                "sold": prod.get("labelGroups", [{}])[0].get("title", ""),
                                "rating": prod.get("averageRating", 0),
                                "review_count": prod.get("totalReview", 0),
                                "average_rating": prod.get("averageRating", 0)
                            })
    
            return {
                "total_products": len(product_list),
                "total_sold": None,
                "products": product_list
            }
    
        return {
            "total_products": 0,
            "total_sold": 0,
            "products": []
        }

    def run(self):
        self.fetch_apollo_state()

        shop_info = self.get_shop_info()
        performance = self.get_shop_performance()
        rating = self.get_rating_data()
        product_data = self.get_products()

        print("Informasi Toko:")
        for k, v in shop_info.items():
            print(f"{k.replace('_', ' ').capitalize()}: {v}")
        for k, v in performance.items():
            print(f"{k.replace('_', ' ').capitalize()}: {v}")
        print(f"Rating Toko: {rating['average_rating']}")
        print(f"Total Ulasan: {rating['total_reviews']}")
        print("Distribusi Rating:")
        for star in range(5, 0, -1):
            print(f"  {star} bintang: {rating['rating_distribution'].get(star, 0)}")

        print("\nProduk:")
        print(f"Total Produk: {product_data['total_products']}")
        print(f"Total Terjual: {product_data['total_sold']}")
        for p in product_data["products"]:
            print(f"- {p['name']}")
            print(f"  Stok: {p['stock']}, Terjual: {p['sold']}, Rating: {p['rating']} ({p['average_rating']}), Ulasan: {p['review_count']}")


if __name__ == "__main__":
    scraper = TokopediaShopScraper(input("Masukkan username toko: "))
    scraper.run()