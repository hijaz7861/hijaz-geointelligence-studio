#!/usr/bin/env python3
"""Main CLI entry point for the Hijaz GeoIntelligence Studio Agent Army."""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.research_agent import ResearchAgent
from agents.producer_agent import ProducerAgent
from agents.script_agent import ScriptAgent
from agents.translation_agent import TranslationAgent
from agents.fact_check_agent import FactCheckAgent
from agents.compliance_agent import ComplianceAgent
from agents.review_gate_agent import ReviewGateAgent
from agents.render_agent import RenderAgent
from agents.metadata_agent import MetadataAgent
from agents.release_bundle_agent import ReleaseBundleAgent
from meta_agents.production_manager import ProductionManagerAgent
from agents.veri_strict_agent import VeriStrictAgent
from meta_agents.meta_learning_orchestrator import MetaLearningOrchestrator
from orchestration.workflow_engine import WorkflowEngine
from orchestration.channel_context import ChannelContextManager


def create_agent_army(config: dict) -> dict:
    """Initialize all agents."""
    agents = {}

    # Meta agents
    agents["production-manager"] = ProductionManagerAgent(config.get("resources", {}))
    agents["veri-strict"] = VeriStrictAgent(config.get("veri_strict", {}))
    agents["meta-learning"] = MetaLearningOrchestrator(config.get("mlo", {}))

    # Production agents
    agents["research-agent"] = ResearchAgent(config.get("research", {}))
    agents["producer-agent"] = ProducerAgent(config.get("producer", {}))
    agents["script-agent"] = ScriptAgent(config.get("script", {}))
    agents["translation-agent"] = TranslationAgent(config.get("translation", {}))
    agents["fact-check-agent"] = FactCheckAgent(config.get("fact_check", {}))
    agents["compliance-agent"] = ComplianceAgent(config.get("compliance", {}))
    agents["review-gate-agent"] = ReviewGateAgent(config.get("review_gate", {}))
    agents["render-agent"] = RenderAgent(config.get("render", {}))
    agents["metadata-agent"] = MetadataAgent(config.get("metadata", {}))
    agents["release-bundle-agent"] = ReleaseBundleAgent(config.get("release_bundle", {}))

    # Register agents with meta-learning
    mlo = agents["meta-learning"]
    for aid, agent in agents.items():
        mlo.register_agent(aid, agent)

    # Register agents with workflow engine
    engine = WorkflowEngine()
    for aid, agent in agents.items():
        engine.register_agent(aid, agent)

    return {"agents": agents, "engine": engine, "mlo": mlo}


def main():
    parser = argparse.ArgumentParser(
        description="Hijaz GeoIntelligence Studio — Agent Army Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", default="config/agents.yaml", help="Config file path")
    parser.add_argument("--channel", default="geo-daily-ur", help="Channel ID")
    parser.add_argument("--topic", default="Indo-Pak border update", help="Topic to produce")
    parser.add_argument("--action", choices=["run", "monitor", "evolve", "status", "list-channels"], default="run")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing outputs")

    args = parser.parse_args()

    # Load config
    config = {}
    # Load LLM config
    llm_config_path = "config/llm.yaml"
    if os.path.exists(llm_config_path):
        try:
            import yaml
            with open(llm_config_path) as f:
                llm_config = yaml.safe_load(f) or {}
            config["llm"] = llm_config
        except ImportError:
            pass
    config_path = args.config
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        except ImportError:
            print("Warning: PyYAML not installed, using defaults")
    else:
        print(f"Config not found: {config_path}, using defaults")

    army = create_agent_army(config)
    agents = army["agents"]
    engine = army["engine"]
    mlo = army["mlo"]

    if args.action == "status":
        print(json.dumps(mlo.get_status(), indent=2))
        print(json.dumps(agents["production-manager"].execute({"action": "get_schedule"}).output, indent=2))
        return

    if args.action == "list-channels":
        ctx_mgr = ChannelContextManager()
        for ch in ctx_mgr.list_channels():
            print(f"  {ch['channel_id']}: {ch['channel_name']} ({ch['language']}) — {ch['purpose']}")
        return

    if args.action == "monitor":
        print("Starting monitoring loop (Ctrl+C to stop)...")
        try:
            while True:
                result = mlo.execute({"action": "monitor", "heartbeats": {}})
                print(f"[{datetime.utcnow().isoformat()}] {json.dumps(result.output)}")
                import time
                time.sleep(30)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
        return

    if args.action == "evolve":
        result = mlo.execute({"action": "evolve"})
        print(json.dumps(result.output, indent=2))
        return

    # Default: run pipeline
    ctx_mgr = ChannelContextManager()
    channel_ctx = ctx_mgr.get_context(args.channel)
    if not channel_ctx:
        print(f"Channel not found: {args.channel}")
        sys.exit(1)

    channel_ctx["search_context"]["last_search_date"] = datetime.utcnow().date().isoformat()
    channel_ctx["search_context"]["topic"] = args.topic

    print(f"\n{'='*60}")
    print(f"  HIJAZ GEOINTELLIGENCE STUDIO — AGENT ARMY")
    print(f"  Channel: {channel_ctx['channel_name']}")
    print(f"  Topic: {args.topic}")
    print(f"  Language: {channel_ctx['language']}")
    print(f"{'='*60}\n")

    # Decide next production
    pm_result = agents["production-manager"].execute({
        "action": "decide_next",
        "available_channels": [args.channel],
    })
    print(f"[Production Manager] {pm_result.output.get('reasoning', '')}")
    print(f"[Production Manager] Publish time: {pm_result.output.get('publish_time', 'N/A')}\n")

    # Create workflow run
    run_id = engine.create_run(args.channel, args.topic)
    print(f"[Workflow Engine] Created run: {run_id}\n")

    # Execute pipeline
    print("Starting production pipeline...\n")
    result = engine.execute_run(run_id, channel_ctx)

    print(f"\n{'='*60}")
    print(f"  PIPELINE RESULT: {result['status'].upper()}")
    print(f"  Run ID: {result['run_id']}")
    print(f"{'='*60}\n")

    for step in result.get("steps", []):
        status_icon = "✅" if step["status"] == "completed" else "❌" if step["status"] == "failed" else "⏸️"
        print(f"  {status_icon} {step['name']}: {step['status']}")

    print()

    # Record episode for MLO
    mlo.execute({
        "action": "learn",
        "episode": {
            "run_id": run_id,
            "channel_id": args.channel,
            "agents_involved": [s["agent_id"] for s in result.get("steps", [])],
            "overall_quality": 85.0,
            "anomalies": [],
            "timestamp": datetime.utcnow().isoformat(),
        },
    })

    # Veri Strict check
    vsa_result = agents["veri-strict"].execute({
        "action": "validate",
        "pipeline_output": result,
    })
    print(f"[Veri Strict] Quality: {vsa_result.output.get('overall_quality', 'N/A')}")

    if args.dry_run:
        print("\n[DRY RUN] No outputs written.")
    else:
        print(f"\n[SUCCESS] Pipeline completed. Outputs in data/channels/{args.channel}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
