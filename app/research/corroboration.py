"""Editorial corroboration warnings; never automatically declare claims true."""
from __future__ import annotations
from urllib.parse import urlparse
from typing import Any

def assess_corroboration(claims: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    by_url = {item.get("url"): item for item in sources if isinstance(item, dict) and isinstance(item.get("url"), str)}
    warnings: list[dict[str, str]] = []
    for claim in claims:
        if not isinstance(claim, dict) or not isinstance(claim.get("claim"), str):
            continue
        text = claim["claim"].strip()
        if not text:
            continue
        refs = [by_url[url] for url in claim.get("source_urls", []) if url in by_url]
        independent_domains = set()
        for source in refs:
            if source.get("source_type") == "independent_reporting":
                host = urlparse(source.get("url", "")).hostname
                if host:
                    independent_domains.add(host.lower().removeprefix("www."))
        if claim.get("status") == "unverified":
            warnings.append({"claim": text, "code": "unverified", "message": "Claim is still labelled unverified; resolve or remove it before release."})
        if not independent_domains:
            warnings.append({"claim": text, "code": "no_independent_reporting", "message": "No independent-reporting source is linked; check whether independent corroboration is available."})
        elif len(independent_domains) == 1:
            warnings.append({"claim": text, "code": "single_independent_domain", "message": "Only one independent-reporting domain is linked; seek a separate source where practical."})
    return warnings
