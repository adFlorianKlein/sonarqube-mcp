# sonarqube-mcp

Ein MCP-Server, der die SonarQube Web API dynamisch als Tools bereitstellt. Er liest zur Startzeit alle verfügbaren Endpunkte von `/api/webservices/list` und generiert daraus eine OpenAPI-Spec, die via [FastMCP](https://github.com/jlowin/fastmcp) als MCP-Tools exponiert wird.

## Voraussetzungen

- Python >= 3.14 (oder Docker)
- SonarQube-Instanz mit API-Token

## Konfiguration

Kopiere `example.env` nach `.env` und passe die Werte an:

| Variable              | Beschreibung                                              | Default           |
|-----------------------|-----------------------------------------------------------|-------------------|
| `SONARQUBE_BASE_URL`  | URL deiner SonarQube-Instanz                              | –                 |
| `SONARQUBE_TOKEN`     | API-Token                                                 | –                 |
| `SONARQUBE_TOOLSETS`  | Komma-getrennte Liste von API-Gruppen (z. B. `issues,rules`). Leer = alle | alle |
| `SONARQUBE_READ_ONLY` | Nur GET-Endpunkte exposieren (`true`/`false`)             | `false`           |
| `MCP_HOST`            | Bind-Adresse (`0.0.0.0` im Container)                    | `127.0.0.1`       |
| `MCP_PORT`            | Port des MCP-Servers                                      | `8070`            |
| `MCP_TRANSPORT`       | Transport-Protokoll (`streamable-http` oder `http`)       | `streamable-http` |

## Starten

**Lokal (uv):**
```bash
uv run python src/sonarqube_mcp/server.py
```

**Docker:**
```bash
docker compose up
```

> Beim Docker-Betrieb `MCP_HOST=0.0.0.0` setzen.

## OpenAPI-Spec generieren (optional)

```bash
uv run python src/sonarqube_mcp/generate_openapi.py
# Ausgabe: sonarqube_openapi.json (konfigurierbar via OUTPUT_FILE)
```
