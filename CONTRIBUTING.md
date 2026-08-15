# Guía de contribución

Alfred Dev es un plugin de Claude Code: 10 agentes, 11 skills planas, 18 comandos publicados, hooks y un núcleo Python. Esta guía resume cómo contribuir. El detalle operativo está en [docs/contributing.md](docs/contributing.md).

## Requisitos previos

- Python 3.10 o superior.
- Claude Code instalado y configurado.
- git.

El runtime Python usa la biblioteca estándar. `requirements.txt` declara FastMCP (`mcp`) como dependencia opcional del servidor de memoria.

## Superficie 0.7.0

```
alfred-dev/
  .claude-plugin/         # plugin.json (18 comandos) y marketplace.json
  agents/                 # 10 agentes (8 de núcleo + Selina + Lucius)
  commands/               # 18 slash /alfred-dev:* + helpers internos
  skills/                 # 11 skills planas (SKILL.md)
  hooks/                  # 10 scripts del ciclo de vida + hooks.json
  core/                   # Motor de orquestación, memoria e informes
  mcp/                    # Servidor MCP stdio (memoria persistente)
  templates/              # 8 plantillas de artefactos
  tests/                  # Tests y contratos de release (pytest)
```

La entrada pública es `/alfred-dev:alfred`. No hay alias global `/alfred`.

## Cómo validar

```bash
python3 -m pytest tests/ -q
python3 scripts/release_audit.py
```

Si el cambio toca la superficie pública, revisa también `README.md`, `docs/` y los tests de contrato (`test_public_surface_contract.py`, `test_version_consistency.py`).

## Añadir un componente

- **Agente:** `agents/<nombre>.md` con frontmatter (`name`, `description`, `model: inherit`, `tools`). Claude Code los descubre desde `agents/`. No hace falta registrarlos en `plugin.json`.
- **Skill:** `skills/<nombre>/SKILL.md` con `name` coincidente. Si tiene efectos laterales, `disable-model-invocation: true`.
- **Comando publicado:** `commands/<nombre>.md` y añadirlo a `.claude-plugin/plugin.json`.
- **Hook:** script en `hooks/` y registro en `hooks/hooks.json` (`command` + `args`). Tests en `tests/test_<nombre>.py`.

Más detalle: [docs/contributing.md](docs/contributing.md), [docs/release.md](docs/release.md).
