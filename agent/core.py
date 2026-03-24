"""
Núcleo del agente optimizador de queries Informix.
Usa Claude Opus 4.6 con adaptive thinking para análisis profundo.
"""

import anthropic
from pathlib import Path
from .prompts import SYSTEM_PROMPT

DB_ESQUEMA_DIR = Path(__file__).parent.parent / "db-esquema"


def load_schema(schema_dir: Path = None) -> tuple[str | None, list[str]]:
    """
    Carga todos los archivos .sql de la carpeta db-esquema/.

    Returns:
        (schema_text, archivos_cargados)
        schema_text es None si no se encontró ningún archivo.
    """
    folder = schema_dir or DB_ESQUEMA_DIR

    if not folder.exists():
        return None, []

    sql_files = sorted(folder.glob("*.sql"))
    if not sql_files:
        return None, []

    parts = []
    loaded = []
    for sql_file in sql_files:
        content = sql_file.read_text(encoding="utf-8").strip()
        if content:
            parts.append(f"-- === {sql_file.name} ===\n{content}")
            loaded.append(sql_file.name)

    if not parts:
        return None, []

    return "\n\n".join(parts), loaded


def build_user_message(query: str, schema: str | None, loaded_files: list[str]) -> str:
    """Construye el mensaje de usuario con el query y el esquema."""
    parts = []

    if schema:
        files_list = ", ".join(loaded_files)
        parts.append(f"""## ESQUEMA COMPLETO DE LA BASE DE DATOS
Archivos cargados desde `db-esquema/`: {files_list}

```sql
{schema}
```

""")
    else:
        parts.append(
            "**Nota:** No se encontraron archivos .sql en la carpeta `db-esquema/`. "
            "El análisis se realizará basándose únicamente en el query. "
            "Para un análisis más preciso, coloca los archivos de esquema en `db-esquema/`.\n\n"
        )

    parts.append(f"""## QUERY A OPTIMIZAR

```sql
{query.strip()}
```

Analiza este query Informix contra el esquema provisto. Identifica todos los problemas de rendimiento \
(joins sin índices, subconsultas correlacionadas, funciones en columnas indexadas, agregaciones sin filtros, \
SELECT *, etc.) y genera la versión optimizada siguiendo el formato de respuesta indicado.""")

    return "".join(parts)


def optimize_query(
    query: str,
    schema_dir: Path = None,
    stream_output: bool = True,
) -> str:
    """
    Analiza y optimiza un query Informix usando Claude.

    Args:
        query: El SQL a optimizar.
        schema_dir: Carpeta con archivos .sql del esquema. Por defecto usa db-esquema/.
        stream_output: Si True, imprime la respuesta en tiempo real (streaming).

    Returns:
        El texto completo de la respuesta del agente.
    """
    schema, loaded_files = load_schema(schema_dir)
    user_message = build_user_message(query, schema, loaded_files)

    client = anthropic.Anthropic()

    if stream_output:
        return _optimize_streaming(client, user_message)
    else:
        return _optimize_blocking(client, user_message)


def _optimize_streaming(client: anthropic.Anthropic, user_message: str) -> str:
    """Ejecuta la optimización con streaming (imprime en tiempo real)."""
    full_response = []

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8192,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for event in stream:
            if hasattr(event, "type") and event.type == "content_block_delta":
                delta = event.delta
                if hasattr(delta, "type") and delta.type == "text_delta":
                    print(delta.text, end="", flush=True)
                    full_response.append(delta.text)

        print()

    return "".join(full_response)


def _optimize_blocking(client: anthropic.Anthropic, user_message: str) -> str:
    """Ejecuta la optimización sin streaming (espera respuesta completa)."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text_blocks = [b.text for b in response.content if b.type == "text"]
    return "\n".join(text_blocks)
