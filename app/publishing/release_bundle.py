"""Create a deterministic release evidence report; never publish or upload content."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from app.editorial.script_validator import ProjectValidationError, release_blockers, validate_project_file
from app.research.claim_ledger import DEFAULT_CLAIMS, ClaimLedgerError, load_claims
from app.research.source_ledger import DEFAULT_LEDGER, SourceLedgerError, load_sources
from app.video.render_validator import RenderValidationError, inspect_rendered_video
from app.voice.srt_validator import SubtitleValidationError, validate_srt_file
class ReleaseBundleError(ValueError):
    """Raised when the evidence bundle inputs cannot be read or serialized."""
def sha256_file(path: str | Path) -> str:
    digest=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""): digest.update(chunk)
    return digest.hexdigest()
def _file_evidence(path: str | Path | None, label: str) -> dict[str, Any]:
    if path is None: return {"label":label,"provided":False,"exists":False,"sha256":None,"size_bytes":None}
    item=Path(path).expanduser().resolve()
    if not item.is_file(): return {"label":label,"provided":True,"exists":False,"path":str(item),"sha256":None,"size_bytes":None}
    return {"label":label,"provided":True,"exists":True,"path":str(item),"sha256":sha256_file(item),"size_bytes":item.stat().st_size}
def build_release_bundle(project_path: str | Path, *, source_path: str | Path = DEFAULT_LEDGER, claims_path: str | Path | None = None, render_path: str | Path | None = None, subtitle_path: str | Path | None = None, metadata_path: str | Path | None = None, min_width: int = 1280, min_height: int = 720) -> dict[str, Any]:
    blockers: list[str]=[]
    try:
        project=validate_project_file(project_path,claims_path,source_path)
        claims=load_claims(claims_path,source_path) if claims_path is not None else load_claims(source_path=source_path)
        sources=load_sources(source_path)
    except (ProjectValidationError,ClaimLedgerError,SourceLedgerError,OSError,ValueError) as exc:
        raise ReleaseBundleError(f"Cannot build release bundle from invalid project/ledgers: {exc}") from exc
    blockers.extend(release_blockers(project,claims))
    linked={item["claim"] for item in claims if item.get("claim") in project.get("claim_ids",[])}
    if len(linked)!=len(project.get("claim_ids",[])): blockers.append("One or more project claim references could not be resolved.")
    source_by_url={item["url"]:item for item in sources}
    claim_by_text={item["claim"]:item for item in claims}
    claim_evidence=[]
    for text in project.get("claim_ids",[]):
        claim=claim_by_text.get(text)
        if not claim: continue
        refs=[]
        for url in claim.get("source_urls",[]):
            source=source_by_url.get(url)
            refs.append({"url":url,"in_source_ledger":source is not None,"title":source.get("title") if source else None,"source_type":source.get("source_type") if source else None,"published_at":source.get("published_at") if source else None})
            if source is None: blockers.append(f"Claim source is missing from source ledger: {url}")
        claim_evidence.append({"claim":text,"status":claim.get("status"),"sources":refs,"notes":"Source linkage is metadata evidence, not independent factual verification."})
    media_evidence=[]
    for asset in project.get("media_assets",[]):
        rights=asset.get("rights_status")
        media_evidence.append({"asset_id":asset.get("asset_id"),"origin_url":asset.get("origin_url"),"rights_status":rights,"creator":asset.get("creator"),"attribution":asset.get("attribution"),"usage_scope":asset.get("usage_scope"),"rights_evidence":asset.get("rights_evidence"),"notes":asset.get("notes")})
        if rights in {"licensed","permission_granted","public_domain_verified","original"}:
            if not str(asset.get("rights_evidence","")).strip(): blockers.append(f"Media asset {asset.get('asset_id')} has no rights evidence text.")
            evidence_text = str(asset.get("rights_evidence","")).strip().lower()
            placeholder_terms = ("synthetic", "fixture", "placeholder", "unknown", "n/a", "not a real license", "not verified", "none")
            if not evidence_text or any(term in evidence_text for term in placeholder_terms): blockers.append(f"Media asset {asset.get('asset_id')} rights evidence appears to be a placeholder or requires manual verification.")
    effective_claims_path = claims_path if claims_path is not None else DEFAULT_CLAIMS
    inputs=[
        _file_evidence(project_path,"project"),
        _file_evidence(source_path,"source_ledger"),
        _file_evidence(effective_claims_path,"claim_ledger"),
        _file_evidence(render_path,"rendered_video"),
        _file_evidence(subtitle_path,"subtitle_file"),
        _file_evidence(metadata_path,"youtube_metadata_draft"),
    ]
    render_report=None
    if render_path is None or not Path(render_path).expanduser().is_file():
        blockers.append("Final rendered video is missing.")
    else:
        try: render_report=inspect_rendered_video(render_path,require_audio=True,require_subtitles=True,min_width=min_width,min_height=min_height)
        except (RenderValidationError,OSError) as exc: blockers.append(f"Rendered video technical validation failed: {exc}")
    subtitle_report=None
    if subtitle_path is None or not Path(subtitle_path).expanduser().is_file():
        blockers.append("Subtitle file is missing.")
    else:
        try:
            cues=validate_srt_file(subtitle_path)
            subtitle_duration_ms = max(c.end_ms for c in cues)
            subtitle_report = {
                "validation": "PASS",
                "cue_count": len(cues),
                "duration_ms": subtitle_duration_ms,
                "note": "Structure/timing only; linguistic accuracy and audio synchronization need human review.",
            }
            if render_report is not None:
                duration_seconds = render_report.get("duration_seconds") if isinstance(render_report, dict) else None
                if isinstance(duration_seconds, bool) or not isinstance(duration_seconds, (int, float)) or not math.isfinite(float(duration_seconds)) or duration_seconds <= 0:
                    blockers.append("Rendered video duration is unavailable for subtitle timeline comparison.")
                else:
                    render_duration_ms = round(float(duration_seconds) * 1000)
                    timeline_within_render = subtitle_duration_ms <= render_duration_ms + 250
                    subtitle_report["render_duration_ms"] = render_duration_ms
                    subtitle_report["timeline_within_render"] = timeline_within_render
                    if not timeline_within_render:
                        overrun_ms = subtitle_duration_ms - render_duration_ms
                        blockers.append(f"Subtitle timeline exceeds rendered video duration by {overrun_ms} ms.")
        except (SubtitleValidationError,OSError) as exc: blockers.append(f"Subtitle validation failed: {exc}")
    if metadata_path is None or not Path(metadata_path).expanduser().is_file():
        blockers.append("YouTube metadata draft is missing.")
    else:
        try:
            metadata=json.loads(Path(metadata_path).read_text(encoding="utf-8"))
            if not isinstance(metadata, dict): blockers.append("Metadata draft must be a JSON object.")
            else:
                if metadata.get("publish_ready") is not False: blockers.append("Metadata draft must explicitly keep publish_ready=false.")
                if metadata.get("release_blockers"): blockers.append("Metadata draft still reports release blockers.")
        except (OSError,UnicodeError,json.JSONDecodeError) as exc: blockers.append(f"Metadata draft is unreadable JSON/UTF-8: {exc}")
    if not project.get("media_assets"): blockers.append("No media assets are listed in the project manifest.")
    approval=project.get("approval",{})
    human_approval={key:approval.get(key) for key in ("script_reviewed","translation_reviewed","media_rights_reviewed","final_video_reviewed","approved_by")}
    blockers.append("This evidence bundle is a review artifact only; it never grants permission to publish or upload.")
    return {
      "schema_version":"1.0","project_id":project["project_id"],"title":project["title"],"language":project["language"],
      "created_utc_note":"Timestamp intentionally omitted to keep the evidence report reproducible for identical inputs.",
      "structural_validation":"PASS","publish_ready":False,"release_status":"draft_blocked",
      "release_blockers":list(dict.fromkeys(blockers)),"input_files":inputs,
      "claim_evidence":claim_evidence,"media_rights_evidence":media_evidence,
      "render_validation":render_report,"subtitle_validation":subtitle_report,
      "human_approval_record":human_approval,
      "counts":{"source_records":len(sources),"claim_records":len(claims),"linked_claims":len(claim_evidence),"media_assets":len(media_evidence)},
      "limitations":["Hashes show which files were inspected, not that their contents are true.","Rights fields and supplied evidence are not legal verification.","Render checks do not assess narration quality, caption accuracy, or synchronization.","Human approval is recorded from project metadata and is not authenticated by this tool.","This bundle does not publish, upload, or authorize public release."]
    }
def write_release_bundle(bundle: dict[str, Any], output_path: str | Path, *, overwrite: bool = False) -> Path:
    output=Path(output_path).expanduser().resolve()
    if output.exists() and not overwrite: raise ReleaseBundleError(f"Output already exists: {output}")
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        import tempfile
        with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=output.parent,prefix=f".{output.name}.",suffix=".tmp",delete=False) as stream:
            temporary=Path(stream.name); json.dump(bundle,stream,ensure_ascii=False,indent=2,sort_keys=True); stream.write("\n")
        if output.exists() and not overwrite: raise ReleaseBundleError(f"Output appeared during generation: {output}")
        temporary.replace(output)
    except OSError as exc: raise ReleaseBundleError(f"Cannot write release bundle: {exc}") from exc
    finally:
        if temporary is not None and temporary.exists(): temporary.unlink()
    return output
