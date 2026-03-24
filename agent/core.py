"""
Núcleo del agente optimizador de queries Informix.
Usa Claude Opus 4.6 con adaptive thinking para análisis profundo.
"""

import anthropic
from pathlib import Path
from .prompts import SYSTEM_PROMPT

DEFAULT_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "seguros.sql"


def load_schema(schema_path: Path = None) -> str | None:
    """Carga el esquema SQL desde archivo. Retorna None si no existe."""
    path = schema_path or DEFAULT_SCHEMA_PATH
    if path.exists():
        content = path.read_text(encoding="utf-8")
        return content
    return None


def build_user_message(query: str, schema: str | None) -> str:
    """Construye el mensaje de usuario con el query y el esquema."""
    parts = []

    if schema:
        parts.append(f"""## ESQUEMA DE LA BASE DE DATOS

```sql
{schema}
```

""")
    else:
        parts.append(
            "**Nota:** No se encontró el archivo de esquema en `schemas/seguros.sql`. "
            "El análisis se realizará basándose únicamente en el query. "
            "Para un análisis más preciso, coloca tu archivo de esquema en `schemas/seguros.sql`.\n\n"
        )

    parts.append(f"""## QUERY A OPTIMIZAR

```sql
{query.strip()}
```

Analiza este query Informix, identifica todos los problemas de rendimiento y genera la versión optimizada siguiendo el formato de respuesta indicado.""")

    return "".join(parts)


def optimize_query(
    query: str,
    schema_path: Path = None,
    stream_output: bool = True,
) -> str:
    """
    Analiza y optimiza un query Informix usando Claude.

    Args:
        query: El SQL a optimizar.
        schema_path: Ruta al archivo .sql con el esquema. Por defecto usa schemas/seguros.sql.
        stream_output: Si True, imprime la respuesta en tiempo real (streaming).

    Returns:
        El texto completo de la respuesta del agente.
    """
    schema = load_schema(schema_path)
    user_message = build_user_message(query, schema)

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
            # Solo imprimir bloques de texto (no los bloques de thinking internos)
            if hasattr(event, "type") and event.type == "content_block_delta":
                delta = event.delta
                if hasattr(delta, "type") and delta.type == "text_delta":
                    print(delta.text, end="", flush=True)
                    full_response.append(delta.text)

        # Salto de línea al final
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
