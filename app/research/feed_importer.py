"""Import RSS/Atom item metadata from explicitly configured HTTPS feeds safely."""
from __future__ import annotations
import email.utils
import ipaddress
import json
import socket
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any
from app.research.source_ledger import DEFAULT_LEDGER, SOURCE_TYPES, CLAIM_STATUSES, SourceLedgerError, add_source
MAX_FEED_BYTES = 2 * 1024 * 1024
DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "research_feeds.json"
class FeedImportError(ValueError):
    """Raised when feed configuration or network response is unsafe/invalid."""
class SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, expected_host: str):
        super().__init__(); self.expected_host = expected_host.lower()
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed=urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() != self.expected_host:
            raise FeedImportError("Feed redirect to a different host or non-HTTPS URL was blocked.")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def _validate_feed_url(url: str) -> urllib.parse.ParseResult:
    parsed=urllib.parse.urlparse(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise FeedImportError("Feed URLs must use HTTPS and include a hostname.")
    try: port = parsed.port
    except ValueError as exc: raise FeedImportError("Feed URL contains an invalid port.") from exc
    if parsed.username or parsed.password or port not in (None,443):
        raise FeedImportError("Feed URLs cannot contain credentials or non-standard ports.")
    host=parsed.hostname.lower()
    if host in {"localhost","localhost.localdomain"} or host.endswith((".localhost",".local",".internal")):
        raise FeedImportError("Local or internal hostnames are not allowed for feed import.")
    try: ip=ipaddress.ip_address(host)
    except ValueError: ip=None
    if ip is not None and not ip.is_global:
        raise FeedImportError("Non-public IP addresses are not allowed for feed import.")
    try: resolved=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
    except OSError as exc: raise FeedImportError(f"Cannot resolve feed hostname {host!r}: {exc}") from exc
    if not resolved: raise FeedImportError(f"Feed hostname {host!r} resolved to no addresses.")
    for entry in resolved:
        address=entry[4][0].split("%",1)[0]
        try: resolved_ip=ipaddress.ip_address(address)
        except ValueError as exc: raise FeedImportError("DNS returned an invalid IP address.") from exc
        if not resolved_ip.is_global:
            raise FeedImportError(f"Feed hostname {host!r} resolves to a non-public IP address; request blocked.")
    return parsed

def load_feed_config(path: str | Path = DEFAULT_CONFIG) -> list[dict[str, str]]:
    try: raw=json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise FeedImportError(f"Cannot read feed configuration: {exc}") from exc
    if not isinstance(raw,dict) or not isinstance(raw.get("feeds"),list):
        raise FeedImportError("Feed config must be a JSON object with a feeds array.")
    feeds=[]
    for index,item in enumerate(raw["feeds"],1):
        if not isinstance(item,dict): raise FeedImportError(f"Feed {index} must be an object.")
        name,url=item.get("name"),item.get("url")
        source_type=item.get("source_type","independent_reporting")
        claim_status=item.get("claim_status","independent_reporting")
        if not isinstance(name,str) or not name.strip(): raise FeedImportError(f"Feed {index} needs a non-empty name.")
        if not isinstance(url,str) or not url.strip(): raise FeedImportError(f"Feed {index} needs a non-empty URL.")
        _validate_feed_url(url.strip())
        if source_type not in SOURCE_TYPES: raise FeedImportError(f"Feed {index} has unsupported source_type.")
        if claim_status not in CLAIM_STATUSES: raise FeedImportError(f"Feed {index} has unsupported claim_status.")
        feeds.append({"name":name.strip(),"url":url.strip(),"source_type":source_type,"claim_status":claim_status})
    return feeds

def _fetch_feed(url: str, timeout_seconds: int = 12) -> bytes:
    parsed=_validate_feed_url(url)
    request=urllib.request.Request(url,headers={"User-Agent":"HijazGeoIntelligenceStudio/0.1 (+feed metadata import)","Accept":"application/rss+xml, application/atom+xml, application/xml, text/xml"})
    opener=urllib.request.build_opener(SameHostRedirectHandler(parsed.hostname or ""))
    try:
        with opener.open(request,timeout=timeout_seconds) as response:
            final=urllib.parse.urlparse(response.geturl())
            if final.scheme != "https" or (final.hostname or "").lower() != (parsed.hostname or "").lower():
                raise FeedImportError("Final feed URL differs from the configured HTTPS host.")
            data=response.read(MAX_FEED_BYTES+1)
    except FeedImportError: raise
    except (OSError,urllib.error.URLError,TimeoutError) as exc:
        raise FeedImportError(f"Could not fetch feed {url}: {exc}") from exc
    if len(data)>MAX_FEED_BYTES: raise FeedImportError(f"Feed exceeded the {MAX_FEED_BYTES}-byte limit.")
    return data

def _text(parent: ET.Element, names: tuple[str,...], namespaces: dict[str,str] | None = None) -> str:
    for name in names:
        node=parent.find(name,namespaces or {})
        if node is not None and node.text and node.text.strip(): return node.text.strip()
    return ""

def _parse_date(value: str) -> str | None:
    if not value: return None
    try:
        parsed=email.utils.parsedate_to_datetime(value)
        if parsed is not None: return parsed.date().isoformat()
    except (TypeError,ValueError,OverflowError): pass
    try: return datetime.fromisoformat(value.replace("Z","+00:00")).date().isoformat()
    except (TypeError,ValueError,OverflowError): return None

def parse_feed_items(xml_bytes: bytes) -> list[dict[str,str]]:
    upper = xml_bytes.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise FeedImportError("Feed XML declarations/entities are not accepted.")
    try: root=ET.fromstring(xml_bytes)
    except ET.ParseError as exc: raise FeedImportError(f"Feed XML is malformed: {exc}") from exc
    items=[]
    atom={"a":"http://www.w3.org/2005/Atom"}
    rss_items=root.findall(".//item")
    if rss_items:
        for item in rss_items:
            title=_text(item,("title",)); url=_text(item,("link",)); date_value=_text(item,("pubDate","date")); summary=_text(item,("description","summary"))
            published=_parse_date(date_value)
            if title and url and published: items.append({"title":title,"url":url,"published_at":published,"summary":summary})
        return items
    for item in root.findall(".//a:entry",atom):
        title=_text(item,("a:title",),atom); date_value=_text(item,("a:published","a:updated"),atom); published=_parse_date(date_value); summary=_text(item,("a:summary",),atom)
        url=""
        for link in item.findall("a:link",atom):
            if link.get("rel","alternate")=="alternate" and link.get("href"):
                url=link.get("href").strip(); break
        if title and url and published: items.append({"title":title,"url":url,"published_at":published,"summary":summary})
    return items

def import_feeds(config_path: str | Path = DEFAULT_CONFIG, ledger_path: str | Path = DEFAULT_LEDGER, *, timeout_seconds: int = 12, max_items_per_feed: int = 50) -> dict[str, Any]:
    if timeout_seconds < 1 or max_items_per_feed < 1: raise FeedImportError("timeout_seconds and max_items_per_feed must be positive.")
    feeds=load_feed_config(config_path); added=0; skipped=0; errors=[]; processed=0
    for feed in feeds:
        try: items=parse_feed_items(_fetch_feed(feed["url"],timeout_seconds))
        except FeedImportError as exc:
            errors.append({"feed":feed["name"],"error":str(exc)}); continue
        for item in items[:max_items_per_feed]:
            processed+=1
            parsed=urllib.parse.urlparse(item["url"])
            try: article_port=parsed.port
            except ValueError: skipped+=1; continue
            host=(parsed.hostname or "").lower()
            if parsed.scheme.lower() not in {"http","https"} or not host or parsed.username or parsed.password or article_port not in (None,80,443) or host in {"localhost","localhost.localdomain"} or host.endswith((".localhost",".local",".internal")):
                skipped+=1; continue
            try: article_ip=ipaddress.ip_address(host)
            except ValueError: article_ip=None
            if article_ip is not None and not article_ip.is_global:
                skipped+=1; continue
            record={"title":item["title"],"url":item["url"],"published_at":item["published_at"],"source_type":feed["source_type"],"claim_status":feed["claim_status"],"notes":f"Imported from configured feed {feed['name']} ({feed['url']}). RSS/Atom metadata only; article content and factual claims have not been independently verified."}
            try: add_source(record,ledger_path); added+=1
            except SourceLedgerError as exc:
                if "already exists" in str(exc): skipped+=1
                else: errors.append({"feed":feed["name"],"item":item.get("title",""),"error":str(exc)})
    return {"feeds_configured":len(feeds),"items_processed":processed,"sources_added":added,"items_skipped":skipped,"errors":errors,"note":"Feed metadata is a discovery lead, not factual verification. Review sources before using claims."}
