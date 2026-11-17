# atoti-sample

Atoti Python project reproducing the data model and data of the
[Atoti tutorial](https://docs.activeviam.com/engine/python-sdk/6.2/getting_started/tutorial/tutorial),
with:

- [`atoti_observability`](https://docs.activeviam.com/engine/python-sdk/6.2/api/atoti_observability): the traces, metrics and logs
  of the Python application **and** of the Atoti server are sent over OTLP to the local Grafana stack (`../docker-compose.yml`).
- [Atoti Intelligence on Amazon Bedrock](https://docs.activeviam.com/atoti-intelligence/6.2/developer-guide/enable-ai-tools/llm/amazon-bedrock-python).

## Run

```bash
# From the root of the repository: Grafana, Prometheus, Loki, Tempo and the OpenTelemetry Collector.
docker compose up -d

cd atoti-sample
cp .env.example .env   # then fill ATOTI_LICENSE and the AWS keys
uv run --env-file .env atoti-sample
```

- Atoti: <http://localhost:9090>
- Grafana: <http://localhost:3000>, dashboard **Atoti > Atoti sample**, or **Drilldown** for metrics, logs and traces.

## Layout

| File | Content |
| --- | --- |
| `src/atoti_sample/__init__.py` | Entry point: telemetry, session start, data model, sample queries. |
| `src/atoti_sample/data_model.py` | Tables, joins, cube, measures, hierarchies and simulations of the tutorial. |
| `src/atoti_sample/data/` | The tutorial's CSV files. |
| `src/atoti_sample/queries.py` | Queries of the tutorial run at startup, with a custom metric `atoti_sample.query.duration`. |
| `src/atoti_sample/telemetry.py` | OpenTelemetry SDK setup (OTLP over HTTP) and `OTEL_*` defaults inherited by the server. |
| `src/atoti_sample/ai.py` | `AiConfig` for Bedrock built from the environment variables. |

## Notes

- **Package source**: `pyproject.toml` declares ActiveViam's repository as the first uv index, so every `atoti*` package
  is resolved from it and never from PyPI. That repository serves only ActiveViam packages anonymously (it answers `401`
  for the others), so third-party dependencies (pandas, OpenTelemetry...) still come from PyPI.
- **Telemetry services**: `atoti-sample` (Python) and `atoti-sample-server` (Java server, instrumented by the
  OpenTelemetry Java agent that `atoti_observability` adds). Both share the same traces: a `Cube.query` span from
  Python contains the server spans of the MDX query.
- **AI**: requires a license including the `ai-essentials` component. Without `AWS_ACCESS_KEY_ID` and
  `AWS_SECRET_ACCESS_KEY`, the session starts without AI.
