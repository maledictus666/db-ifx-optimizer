"""
Núcleo del agente optimizador de queries Informix.
Usa Claude Opus 4.6 con adaptive thinking para análisis profundo.
"""

import anthropic
from pathlib import Path
from .prompts import SYSTEM_PROMPT
from .schema_parser import get_relevant_schema

DB_ESQUEMA_DIR = Path(__file__).parent.parent / "db-esquema"


def _get_sql_files(schema_dir: Path) -> list[Path]:
    """Retorna los archivos .sql de la carpeta, ordenados."""
    if not schema_dir.exists():
        return []
    return sorted(schema_dir.glob("*.sql"))


def build_user_message(
    query: str,
    schema_text: str,
    tables_found: list[str],
    tables_not_found: list[str],
) -> str:
    """Construye el mensaje de usuario con el DDL relevante y el query."""
    parts = []

    if schema_text:
        found_list = ", ".join(f"`{t}`" for t in tables_found)
        parts.append(f"## ESQUEMA DE TABLAS INVOLUCRADAS\nTablas detectadas en el query: {found_list}\n\n```sql\n{schema_text}\n```\n\n")

    if tables_not_found:
        not_found_list = ", ".join(f"`{t}`" for t in tables_not_found)
        parts.append(
            f"**Advertencia:** Las siguientes tablas del query no se encontraron en el esquema: {not_found_list}. "
            f"El análisis de esas tablas será limitado.\n\n"
        )

    if not schema_text and not tables_not_found:
        parts.append(
            "**Nota:** No se encontraron archivos .sql en `db-esquema/` o no se pudieron "
            "detectar tablas en el query. El análisis se realizará solo con el SQL.\n\n"
        )

    parts.append(
        f"## QUERY A OPTIMIZAR\n\n```sql\n{query.strip()}\n```\n\n"
        "Analiza este query Informix contra el esquema provisto. Identifica todos los problemas "
        "de rendimiento (joins sin índices, subconsultas correlacionadas, funciones en columnas "
        "indexadas, agregaciones sin filtros, SELECT *, etc.) y genera la versión optimizada "
        "siguiendo el formato de respuesta indicado."
    )

    return "".join(parts)


def optimize_query(
    query: str,
    schema_dir: Path = None,
    stream_output: bool = True,
) -> str:
    """
    Analiza y optimiza un query Informix usando Claude.

    Extrae automáticamente las tablas del query y carga solo
    sus DDLs desde db-esquema/, en lugar de enviar el esquema completo.

    Args:
        query: El SQL a optimizar.
        schema_dir: Carpeta con archivos .sql del esquema. Por defecto usa db-esquema/.
        stream_output: Si True, imprime la respuesta en tiempo real (streaming).

    Returns:
        El texto completo de la respuesta del agente.
    """
    folder = schema_dir or DB_ESQUEMA_DIR
    sql_files = _get_sql_files(folder)

    schema_text, tables_found, tables_not_found = get_relevant_schema(query, sql_files)

    user_message = build_user_message(query, schema_text, tables_found, tables_not_found)

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
