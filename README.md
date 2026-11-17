# par-student-agent-observability
Tracing and recording every action of agents

## Content

- [`atoti-sample/`](atoti-sample): Atoti Python project (tutorial data model, `atoti_observability`, Atoti Intelligence on Amazon Bedrock).
- [`docker-compose.yml`](docker-compose.yml): local Grafana stack ([`grafana/otel-lgtm`](https://github.com/grafana/docker-otel-lgtm), all-in-one image) receiving traces (Tempo), metrics (Prometheus) and logs (Loki) over OTLP. [`observability/`](observability) adds an Atoti dashboard to it.

```bash
docker compose up -d                       # Grafana on http://localhost:3000
cd atoti-sample && uv run --env-file .env atoti-sample
```
