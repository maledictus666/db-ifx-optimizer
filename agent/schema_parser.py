"""
Parser del esquema Informix.

Indexa los archivos .sql de db-esquema/ en un diccionario {tabla: ddl}
y extrae solo los DDLs de las tablas que aparecen en un query dado.
"""

import re
from pathlib import Path


# ── Extracción de tablas desde el query ──────────────────────────────────────

# Palabras clave SQL que van seguidas de un nombre de tabla
_TABLE_KEYWORDS = r"""
    (?:FROM|JOIN|INTO|UPDATE|TABLE|OUTER\s+JOIN|LEFT\s+(?:OUTER\s+)?JOIN|
       RIGHT\s+(?:OUTER\s+)?JOIN|INNER\s+JOIN|CROSS\s+JOIN)
"""

_TABLE_PATTERN = re.compile(
    rf"{_TABLE_KEYWORDS}\s+"
    r'(?:"informix"\s*\.\s*)?'          # esquema opcional: "informix".
    r'([a-zA-Z_][a-zA-Z0-9_]*)'         # nombre de tabla
    r'(?:\s+(?:AS\s+)?[a-zA-Z_][a-zA-Z0-9_]*)?',  # alias opcional
    re.IGNORECASE | re.VERBOSE,
)

# Palabras reservadas que NO son nombres de tabla aunque aparezcan después de keyword
_SQL_KEYWORDS = {
    "select", "where", "set", "values", "on", "and", "or", "not",
    "null", "is", "in", "exists", "between", "like", "case", "when",
    "then", "else", "end", "group", "order", "by", "having", "limit",
    "union", "all", "distinct", "as", "with", "recursive",
}


def extract_tables_from_query(query: str) -> list[str]:
    """
    Extrae los nombres de tablas referenciados en un query SQL.
    Retorna lista de nombres en minúsculas, sin duplicados, sin alias.
    """
    tables = set()
    for match in _TABLE_PATTERN.finditer(query):
        name = match.group(1).lower()
        if name not in _SQL_KEYWORDS:
            tables.add(name)
    return sorted(tables)


# ── Indexación del esquema ────────────────────────────────────────────────────

# Detecta el inicio de un bloque CREATE TABLE (con o sin esquema "informix".)
_CREATE_TABLE_RE = re.compile(
    r'^create\s+table\s+(?:"informix"\s*\.\s*)?([a-zA-Z_][a-zA-Z0-9_]*)\s*$',
    re.IGNORECASE,
)

# Detecta CREATE INDEX / CREATE UNIQUE INDEX sobre una tabla
_CREATE_INDEX_RE = re.compile(
    r'^create\s+(?:unique\s+)?index\s+\S+\s+on\s+(?:"informix"\.)?([a-zA-Z_][a-zA-Z0-9_]*)',
    re.IGNORECASE,
)


def _normalize(name: str) -> str:
    return name.strip().lower()


def build_schema_index(sql_files: list[Path]) -> dict[str, list[str]]:
    """
    Lee los archivos .sql y construye un índice:
        { nombre_tabla_lower: [bloque_ddl_tabla, bloque_ddl_indices...] }

    Cada bloque es el texto tal como aparece en el archivo.
    """
    index: dict[str, list[str]] = {}

    for sql_file in sql_files:
        text = sql_file.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]

            # ── CREATE TABLE ──────────────────────────────────────────────
            m = _CREATE_TABLE_RE.match(line.strip())
            if m:
                table_name = _normalize(m.group(1))
                block_lines = [line]
                i += 1
                # Capturar hasta la línea que cierra con ")" o ");"
                while i < len(lines):
                    block_lines.append(lines[i])
                    stripped = lines[i].strip()
                    if stripped in (")", ");") or stripped.startswith(")"):
                        i += 1
                        break
                    i += 1
                block = "\n".join(block_lines)
                if table_name not in index:
                    index[table_name] = []
                index[table_name].append(block)
                continue

            # ── CREATE INDEX ──────────────────────────────────────────────
            m = _CREATE_INDEX_RE.match(line.strip())
            if m:
                table_name = _normalize(m.group(1))
                # El índice es una sola línea (o hasta ";")
                block_lines = [line]
                if ";" not in line:
                    i += 1
                    while i < len(lines):
                        block_lines.append(lines[i])
                        if ";" in lines[i]:
                            i += 1
                            break
                        i += 1
                block = "\n".join(block_lines)
                if table_name not in index:
                    index[table_name] = []
                index[table_name].append(block)
                continue

            i += 1

    return index


# ── API pública ───────────────────────────────────────────────────────────────

def get_relevant_schema(
    query: str,
    sql_files: list[Path],
) -> tuple[str, list[str], list[str]]:
    """
    Dado un query y los archivos de esquema, retorna solo el DDL relevante.

    Returns:
        (schema_text, tablas_encontradas, tablas_no_encontradas)
    """
    tables_in_query = extract_tables_from_query(query)
    if not tables_in_query:
        return "", [], []

    schema_index = build_schema_index(sql_files)

    found = []
    not_found = []
    ddl_blocks = []

    for table in tables_in_query:
        if table in schema_index:
            found.append(table)
            ddl_blocks.extend(schema_index[table])
        else:
            not_found.append(table)

    schema_text = "\n\n".join(ddl_blocks)
    return schema_text, found, not_found
