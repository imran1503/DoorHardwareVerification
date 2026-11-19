"""Refresh research-lead product listings from the configured public catalogs."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
import json
import re
import threading
import time
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from .catalog import PRODUCT_CATEGORIES
from .database import connect


USER_AGENT = "DoorHardwareChecker/0.2 (public catalog listing refresh)"
REQUEST_TIMEOUT_SECONDS = 15
MAX_PAGE_BYTES = 8 * 1024 * 1024
REFRESH_LOCK = threading.Lock()

SOURCES = [
    ("Camden Controls", "https://www.camdencontrols.com/", "Camden Controls", ""),
    ("Camden electric strikes", "https://www.camdencontrols.com/category/Electrified_Locks_Relays_and_Timers/Electric_Strikes", "Camden Controls", "electric_strike"),
    ("Camden restroom kits", "https://www.camdencontrols.com/products/WC_Restroom_Control_Kits", "Camden Controls", "washroom_control"),
    ("ADI door hardware", "https://www.en.adiglobaldistribution.ca/catalog/shopproducts/access-control/door-hardware", "ADI Global Canada", ""),
    ("ADI request to exit", "https://www.en.adiglobaldistribution.ca/catalog/shopproducts/access-control/egress-devices/request-to-exit-devices", "ADI Global Canada", "request_to_exit"),
    ("ADI Camden catalog", "https://www.en.adiglobaldistribution.ca/catalog/shop-brands/camden-door-controls", "ADI Global Canada", ""),
    ("Wesco Canada", "https://buy.wesco.ca/", "Wesco Canada", ""),
    ("BG electric strikes", "https://shop.bgdistribution.ca/category/electric-strikes-and-accessories", "BG Distribution", "electric_strike"),
    ("BG actuators", "https://shop.bgdistribution.ca/category/electric-paddles-and-actuators", "BG Distribution", "activation_device"),
    ("BG request and access", "https://shop.bgdistribution.ca/category/readers-keypads-and-accessories", "BG Distribution", "access_control"),
    ("BG electronic locks", "https://shop.bgdistribution.ca/category/electronic-locks-and-accessories", "BG Distribution", "electric_lock"),
    ("BG power and control", "https://shop.bgdistribution.ca/category/control-boxes-power-supplies-and-accessories", "BG Distribution", "controller"),
    ("BG contacts and rectifiers", "https://shop.bgdistribution.ca/category/contacts-and-rectifiers", "BG Distribution", "door_contact"),
    ("BG door closers", "https://shop.bgdistribution.ca/category/door-closers", "BG Distribution", "closer"),
    ("BG exit devices", "https://shop.bgdistribution.ca/category/exit-devices", "BG Distribution", "exit_device"),
    ("BG hinges and pivots", "https://shop.bgdistribution.ca/category/hinges-and-pivots", "BG Distribution", "hinge"),
    ("BG locks and flush bolts", "https://shop.bgdistribution.ca/category/locks-flush-bolts-and-rollers", "BG Distribution", "mechanical_lock"),
]

LABEL_CATEGORIES = [
    ("restroom control", "washroom_control"), ("washroom control", "washroom_control"),
    ("emergency call", "emergency_call"), ("annunciator", "alarm"), ("door alarm", "alarm"),
    ("request to exit", "request_to_exit"), ("rex", "request_to_exit"),
    ("magnetic door holder", "door_stop"), ("door holder", "door_stop"),
    ("push exit", "activation_device"), ("electric strike", "electric_strike"),
    ("maglock", "electric_lock"), ("magnetic lock", "electric_lock"), ("electronic lock", "electric_lock"),
    ("deadlatch", "mechanical_lock"), ("door handle", "mechanical_lock"),
    ("keypad", "access_control"), ("reader", "access_control"), ("credential", "access_control"),
    ("power supply", "power_supply"), ("transformer", "power_supply"),
    ("door contact", "door_contact"), ("relay", "controller"), ("controller", "controller"),
    ("time delay", "controller"), ("timer", "controller"),
    ("hinge", "hinge"), ("closer", "closer"), ("exit device", "exit_device"),
    ("push plate", "activation_device"), ("actuator", "activation_device"),
    ("touchless", "activation_device"), ("push button", "activation_device"),
    ("pushbutton", "activation_device"), ("key switch", "activation_device"),
    ("pull switch", "activation_device"), ("control station", "activation_device"),
    ("switch", "activation_device"), ("operator", "automatic_operator"),
    ("door seal", "door_seal"), ("threshold", "threshold"), ("flush bolt", "flush_bolt"),
    ("coordinator", "coordinator"), ("mounting post", "other"), ("enclosure", "other"),
]

URL_CATEGORIES = [
    ("electric strike", "electric_strike"), ("request to exit", "request_to_exit"),
    ("magnetic locks", "electric_lock"), ("electrified locks", "electric_lock"),
    ("door closer", "closer"), ("door hinge", "hinge"), ("exit device", "exit_device"),
    ("door push plate", "activation_device"), ("actuator", "activation_device"),
    ("door holder", "door_stop"), ("restroom control", "washroom_control"),
    ("emergency call", "emergency_call"), ("door alarm", "alarm"),
    ("annunciator", "alarm"), ("door control relay", "controller"),
    ("power supply", "power_supply"), ("readers keypads", "access_control"),
    ("door handle", "mechanical_lock"), ("deadlatch", "mechanical_lock"),
    ("hinges and pivots", "hinge"), ("flush bolts", "flush_bolt"),
]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts = []
        self.links = []
        self.in_json = False
        self.script_data = []
        self.anchor = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self.in_json = True
            self.script_data = []
        elif tag == "a":
            self.anchor = {"href": attrs.get("href", ""), "title": attrs.get("title", ""), "text": []}

    def handle_data(self, data):
        if self.in_json:
            self.script_data.append(data)
        if self.anchor is not None:
            self.anchor["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.in_json:
            self.scripts.append("".join(self.script_data))
            self.in_json = False
        elif tag == "a" and self.anchor is not None:
            self.anchor["text"] = " ".join(" ".join(self.anchor["text"]).split())
            if self.anchor["href"]:
                self.links.append(self.anchor)
            self.anchor = None


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _model(value):
    candidates = re.findall(r"(?<![A-Za-z0-9])[A-Z0-9][A-Z0-9./_-]{2,}[A-Z0-9](?![A-Za-z0-9])", str(value or ""), re.I)
    return next((candidate.strip("-./_") for candidate in candidates if re.search(r"\d", candidate)), "")


def _category(url, name, stated):
    label = f"{name or ''}".replace("_", " ").replace("-", " ").lower()
    for term, category in LABEL_CATEGORIES:
        if term in label:
            return category
    path = url.replace("_", " ").replace("-", " ").lower()
    for term, category in URL_CATEGORIES:
        if term in path:
            return category
    return stated


def _manufacturer(supplier, name, model):
    low = f"{name} {model}".lower()
    if supplier == "Camden Controls":
        return supplier
    prefixes = [("cm-", "Camden Controls"), ("cx-", "Camden Controls"), ("camd-", "Camden Controls"),
                ("ru-", "RCI by dormakaba"), ("lcn", "LCN"), ("hager", "Hager"),
                ("dormakaba", "dormakaba"), ("schlage", "Schlage"), ("vd-", "Von Duprin")]
    match = next((brand for prefix, brand in prefixes if model.lower().startswith(prefix)), "")
    if match:
        return match
    brands = ["Camden Controls", "RCI by dormakaba", "LCN", "Kantech", "Hager", "dormakaba", "Schlage", "Von Duprin", "Securitron", "Alarm Controls"]
    return next((brand for brand in brands if brand.lower() in low), "")


def _normalize(item, page_url, supplier, stated, structured=False):
    name = str(item.get("name") or item.get("title") or "").strip()
    sku = str(item.get("sku") or item.get("mpn") or item.get("productID") or "").strip()
    model = _model(name) or sku
    product_url = urljoin(page_url, str(item.get("url") or item.get("@id") or page_url))
    if urlparse(product_url).netloc.lower() != urlparse(page_url).netloc.lower():
        product_url = page_url
    category = _category(product_url, f"{item.get('category', '')} {name}", stated)
    code = (sku or model).upper()
    if code.startswith("CX-WEC"):
        category = "emergency_call"
    elif code.startswith("CX-WC"):
        category = "washroom_control"
    if any(term in name.lower() for term in ("cabinet lock", "marking template", "strike template")):
        return None
    manufacturer = str(item.get("brand", "") or "").strip()
    if isinstance(item.get("brand"), dict):
        manufacturer = str(item["brand"].get("name", "")).strip()
    if manufacturer.lower() in {"camden", "camden door controls"}:
        manufacturer = "Camden Controls"
    manufacturer = manufacturer or _manufacturer(supplier, name, model)
    if category not in PRODUCT_CATEGORIES or not model or not name or not manufacturer:
        return None
    specs = {
        "record_scope": "live_catalog_listing",
        "catalog_source": supplier,
        "catalog_page": page_url,
        "structured_product_data": bool(structured),
    }
    description = item.get("description")
    if isinstance(description, str) and description.strip():
        specs["catalog_description"] = " ".join(description.split())[:2000]
    return {
        "category": category, "manufacturer": manufacturer, "model": model, "name": name,
        "specifications": specs, "source_title": f"Live catalog listing — {supplier}",
        "source_url": product_url, "evidence_status": "research_lead",
        "notes": "Catalog listing confirms listing presence only; it does not establish compatibility. Verify the exact model, suffix, ratings, fit and current availability from manufacturer documentation.",
    }


def _extract(html, page_url, supplier, stated):
    parser = PageParser()
    parser.feed(html)
    records = {}
    for script in parser.scripts:
        try:
            data = json.loads(script)
        except (json.JSONDecodeError, TypeError):
            continue
        for node in _walk(data):
            types = node.get("@type", [])
            if isinstance(types, str):
                types = [types]
            products = [node] if any(str(value).lower() == "product" for value in types) else []
            if str(node.get("@type", "")).lower() == "itemlist":
                products += [entry.get("item", {}) for entry in node.get("itemListElement", []) if isinstance(entry, dict)]
            for item in products:
                record = _normalize(item, page_url, supplier, stated, structured=True)
                if record:
                    records.setdefault((record["category"], record["manufacturer"].lower(), record["model"].lower()), record)
    for link in parser.links:
        href = link["href"]
        product_url = urljoin(page_url, href)
        if urlparse(product_url).netloc.lower() != urlparse(page_url).netloc.lower():
            continue
        name = link["text"] or link["title"]
        path = urlparse(product_url).path.lower()
        if len(name) < 5 or not any(token in path for token in ("/product/", "/products/", "/item/", "/p/")):
            continue
        model = _model(name) or _model(path.rsplit("/", 1)[-1].replace("-", " "))
        record = _normalize({"name": name, "sku": model, "url": product_url}, page_url, supplier, stated)
        if record:
            records.setdefault((record["category"], record["manufacturer"].lower(), record["model"].lower()), record)
    return list(records.values())


def _fetch(source):
    title, url, supplier, category = source
    if urlparse(url).scheme != "https":
        return {"source": title, "url": url, "status": "skipped", "count": 0, "error": "HTTPS required"}, []
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/ld+json;q=0.9,*/*;q=0.5"})
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.lower() and "json" not in content_type.lower():
                return {"source": title, "url": url, "status": "skipped", "count": 0, "error": f"Unsupported content type: {content_type}"}, []
            body = response.read(MAX_PAGE_BYTES + 1)
            if len(body) > MAX_PAGE_BYTES:
                return {"source": title, "url": url, "status": "skipped", "count": 0, "error": "Page exceeded 8 MB limit"}, []
            charset = response.headers.get_content_charset() or "utf-8"
        products = _extract(body.decode(charset, errors="replace"), url, supplier, category)
        return {"source": title, "url": url, "status": "ok" if products else "no_listings", "count": len(products)}, products
    except Exception as error:
        return {"source": title, "url": url, "status": "error", "count": 0, "error": f"{type(error).__name__}: {error}"}, []


def scrape_catalogs():
    products, results = {}, []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(_fetch, source) for source in SOURCES]
        for future in as_completed(futures):
            result, rows = future.result()
            results.append(result)
            for product in rows:
                key = (product["category"], product["manufacturer"].lower(), product["model"].lower())
                products.setdefault(key, product)
    return {"sources": sorted(results, key=lambda row: row["source"]), "products": list(products.values())}


def refresh_catalogs():
    if not REFRESH_LOCK.acquire(blocking=False):
        raise RuntimeError("A catalog refresh is already running.")
    try:
        scrape = scrape_catalogs()
        added = refreshed = unchanged = 0
        with connect() as db:
            for product in scrape["products"]:
                existing = db.execute(
                    "SELECT id,source_title,evidence_status FROM products WHERE category=? AND lower(manufacturer)=lower(?) AND lower(model)=lower(?)",
                    (product["category"], product["manufacturer"], product["model"]),
                ).fetchone()
                specs = json.dumps(product["specifications"])
                if existing:
                    title = existing["source_title"] or ""
                    live = title.startswith("Live catalog listing —")
                    seeded_lead = existing["evidence_status"] == "research_lead" and title.startswith(("ADI Global Canada catalog listing —", "BG Distribution catalog listing —"))
                    if existing["evidence_status"] == "research_lead" and (live or seeded_lead):
                        db.execute(
                            "UPDATE products SET name=?,specifications=?,source_title=?,source_url=?,notes=?,active=1,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                            (product["name"], specs, product["source_title"], product["source_url"], product["notes"], existing["id"]),
                        )
                        refreshed += 1
                    else:
                        unchanged += 1
                    continue
                db.execute(
                    "INSERT INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES (?,?,?,?,?,?,?,?,?)",
                    (product["category"], product["manufacturer"], product["model"], product["name"], specs, product["source_title"], product["source_url"], "research_lead", product["notes"]),
                )
                added += 1
            db.execute(
                "INSERT INTO catalog_scrape_runs(source_results,products_added,products_refreshed,products_unchanged) VALUES (?,?,?,?)",
                (json.dumps(scrape["sources"]), added, refreshed, unchanged),
            )
        return {"sources": scrape["sources"], "products_added": added, "products_refreshed": refreshed, "products_unchanged": unchanged}
    finally:
        REFRESH_LOCK.release()


def refresh_daily():
    while True:
        try:
            result = refresh_catalogs()
            print(f"Live catalog refresh: {result['products_added']} added, {result['products_refreshed']} refreshed.")
        except Exception as error:
            print(f"Live catalog refresh failed: {error}")
        time.sleep(24 * 60 * 60)


