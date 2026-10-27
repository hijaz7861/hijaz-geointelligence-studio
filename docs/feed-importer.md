# RSS/Atom source discovery

The importer collects source metadata as research leads. It does not read the full article, confirm facts, grant media rights, or turn feed text directly into a script.

## Configure feeds

Edit `config/research_feeds.json`. It intentionally starts with an empty list so the project does not silently ingest a publisher's content before its terms are reviewed.

Example structure (replace the placeholder with a publisher-approved feed URL):

```json
{
  "feeds": [
    {
      "name": "Publisher world-news feed",
      "url": "https://publisher.example/rss.xml",
      "source_type": "independent_reporting",
      "claim_status": "independent_reporting"
    }
  ]
}
```

Feed URLs must use HTTPS, have no credentials or non-standard port, and resolve only to public IP addresses. Cross-host or non-HTTPS redirects are rejected. Feed responses are limited to 2 MiB and a configurable request timeout. RSS and Atom items without a usable title, link, or publication date are ignored. Duplicate source URLs are skipped.

## Run

```sh
python scripts/import_feeds.py \
  --config config/research_feeds.json \
  --ledger data/sources/sources.json \
  --timeout-seconds 12 \
  --max-items-per-feed 50
```

Review imported titles and source links before using them in a claim. The ledger notes explicitly say that feed metadata and article facts have not been independently verified. Review each publisher's terms for business use and attribution before configuring a feed. Feed import is a discovery step, not permission to reproduce article text or imagery.

The automated tests use synthetic RSS/Atom fixtures and mocked network responses. No live publisher feed is configured or claimed to have been tested by this repository yet.
