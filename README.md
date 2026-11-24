# Hijaz GeoIntelligence Studio — Agent Army

AI-powered geopolitical research and multilingual documentary production with a fully autonomous agent army.

## What This System Does

- **23 specialized agents** across 5 tiers: Research, Producer, Script, Translation, Fact-Check, Compliance, Render, Metadata, Release Bundle, and more
- **3 meta-agents**: Production Manager (scheduling), Veri Strict (quality guardian), Meta-Learning Orchestrator (continuous improvement)
- **Multi-channel support**: Run multiple YouTube channels in parallel, each with its own topic, language, and audience
- **Full pipeline automation**: Research → Script → Translation → Compliance → Render → Metadata → Release Bundle
- **Human-in-the-loop**: Every consequential step has a review gate; no auto-publish without approval

## Quick Start

```sh
# Setup
sh scripts/setup.sh

# Run pipeline (dry-run)
python3 cli/run_pipeline.py --channel geo-daily-ur --topic "Border update" --dry-run

# List channels
python3 cli/run_pipeline.py --action list-channels

# Check status
python3 cli/run_pipeline.py --action status

# Run monitoring
python3 cli/run_pipeline.py --action monitor

# Run evolution cycle
python3 cli/run_pipeline.py --action evolve
```

## Run with Docker

```sh
docker-compose up -d
```

## Validation

```sh
sh scripts/validate.sh
```

All 169 unit tests + 24 validation stages pass.

## Channels (Pre-configured)

| Channel | Language | Topic | Upload Day |
|---------|----------|-------|------------|
| geo-daily-ur | Urdu | Geopolitics, borders, satellite | Monday |
| tech-tutorials-hi | Hindi | Tech tutorials, mobile tricks | Wednesday |
| islamic-history-ur | Urdu | Islamic history, Urdu literature | Friday |

## Architecture

```
agents/           # 20+ specialized agents
meta_agents/      # Production Manager, Veri Strict, Meta-Learning
orchestration/    # Workflow engine, state manager, channel context
config/           # Channel, resource, agent, policy configs
cli/              # Command-line tools
tests/            # 169+ unit tests
```

## Key Features

- **Context-aware agents**: Each agent knows its channel, purpose, target country, topic, and search date
- **Data isolation**: Each channel has its own sources, claims, and projects
- **Quality scoring**: Every agent output scored 0-100; auto-fix for common errors
- **Cross-agent learning**: Shared knowledge base + experience replay + evolution cycles
- **Resource management**: GPU/CPU/TTS/API budget tracking with alerts
- **Fail-closed**: Any error blocks pipeline; human escalation for high-risk items
- **Deterministic release bundles**: SHA-256 hashes, claim/source traceability, approval records

## License

MIT
