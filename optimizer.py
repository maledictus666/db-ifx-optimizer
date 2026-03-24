#!/usr/bin/env python3
"""
Agente Optimizador de Queries Informix
========================================
Analiza consultas SQL Informix pesadas contra el esquema completo de la base
de datos y genera versiones optimizadas que retornan exactamente los mismos
resultados.

Uso:
    # Modo interactivo (pega el query en la terminal):
    python optimizer.py

    # Query directo por argumento:
    python optimizer.py "SELECT * FROM polizas WHERE ..."

    # Query desde archivo:
    python optimizer.py --file mi_query.sql

    # Carpeta de esquema personalizada:
    python optimizer.py --db /ruta/a/esquemas/ --file mi_query.sql

    # Guardar resultado:
    python optimizer.py --file mi_query.sql --output resultado.md

    # Sin streaming (espera respuesta completa):
    python optimizer.py --no-stream --file mi_query.sql
"""

import argparse
import sys
from pathlib import Path

# Colores ANSI para la terminal
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def print_banner():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════════════╗
║      Agente Optimizador de Queries Informix          ║
║      Powered by Claude Opus 4.6                      ║
╚══════════════════════════════════════════════════════╝{RESET}
""")


def print_schema_status(schema_dir: Path):
    """Muestra qué archivos de esquema se encontraron."""
    if not schema_dir.exists():
        print(f"{YELLOW}⚠  Carpeta '{schema_dir}' no encontrada. "
              f"Ejecutando sin esquema.{RESET}\n")
        return

    sql_files = sorted(schema_dir.glob("*.sql"))
    if not sql_files:
        print(f"{YELLOW}⚠  No hay archivos .sql en '{schema_dir}'. "
              f"Ejecutando sin esquema.{RESET}\n")
        return

    print(f"{GREEN}✓  Esquema cargado desde '{schema_dir}':{RESET}")
    for f in sql_files:
        size_kb = f.stat().st_size / 1024
        print(f"   {DIM}•{RESET} {f.name}  {DIM}({size_kb:.1f} KB){RESET}")
    print()


def read_query_interactive() -> str:
    """Lee el query de forma interactiva desde stdin."""
    print(f"{YELLOW}Pega tu query SQL Informix a continuación.")
    print(f"Cuando termines, presiona Enter y luego Ctrl+Z (Windows) o Ctrl+D (Linux/Mac):{RESET}\n")

    lines = []
    try:
        for line in sys.stdin:
            lines.append(line)
    except KeyboardInterrupt:
        print("\nCancelado.")
        sys.exit(0)

    query = "".join(lines).strip()
    if not query:
        print(f"{YELLOW}No se ingresó ningún query.{RESET}")
        sys.exit(1)

    return query


def read_query_from_file(file_path: str) -> str:
    """Lee el query desde un archivo .sql o .txt."""
    path = Path(file_path)
    if not path.exists():
        print(f"{RED}Error: No se encontró el archivo '{file_path}'{RESET}")
        sys.exit(1)
    return path.read_text(encoding="utf-8").strip()


def main():
    parser = argparse.ArgumentParser(
        description="Optimiza queries SQL Informix usando inteligencia artificial.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="El query SQL a optimizar (entre comillas). Si se omite, modo interactivo.",
    )
    parser.add_argument(
        "--file", "-f",
        metavar="ARCHIVO.sql",
        help="Leer el query desde un archivo .sql",
    )
    parser.add_argument(
        "--db",
        metavar="CARPETA/",
        help="Carpeta con los .sql del esquema (por defecto: db-esquema/)",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Desactivar streaming (esperar respuesta completa antes de mostrar)",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="ARCHIVO.md",
        help="Guardar el resultado en un archivo Markdown",
    )

    args = parser.parse_args()

    print_banner()

    # Resolver carpeta de esquema
    schema_dir = Path(args.db) if args.db else Path("db-esquema")
    print_schema_status(schema_dir)

    # Determinar el query a optimizar
    if args.file:
        query = read_query_from_file(args.file)
        print(f"{GREEN}✓  Query cargado desde: {args.file}{RESET}\n")
    elif args.query:
        query = args.query.strip()
    else:
        query = read_query_interactive()

    if not query:
        print(f"{RED}Error: el query está vacío.{RESET}")
        sys.exit(1)

    # Mostrar el query recibido
    print(f"{CYAN}{BOLD}━━━ QUERY ORIGINAL ━━━{RESET}")
    print(query)
    print(f"{CYAN}{'━' * 40}{RESET}\n")

    # Importar agente
    try:
        from agent.core import optimize_query
    except ImportError as e:
        print(f"{RED}Error al importar el agente: {e}{RESET}")
        print("Asegúrate de tener instaladas las dependencias: pip install -r requirements.txt")
        sys.exit(1)

    # Mostrar preview de tablas detectadas antes de llamar a Claude
    try:
        from agent.schema_parser import extract_tables_from_query
        tables = extract_tables_from_query(query)
        if tables:
            print(f"{CYAN}{BOLD}━━━ TABLAS DETECTADAS EN EL QUERY ━━━{RESET}")
            for t in tables:
                print(f"   {DIM}•{RESET} {t}")
            print()
    except Exception:
        pass  # No interrumpir si el preview falla

    print(f"{CYAN}{BOLD}━━━ ANALIZANDO Y OPTIMIZANDO ━━━{RESET}\n")

    try:
        result = optimize_query(
            query=query,
            schema_dir=schema_dir,
            stream_output=not args.no_stream,
        )
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            print(f"\n{RED}Error de autenticación: configura tu API key de Anthropic.{RESET}")
            print("  Windows (PowerShell): $env:ANTHROPIC_API_KEY = 'tu-api-key'")
            print("  Linux / Mac:          export ANTHROPIC_API_KEY='tu-api-key'")
        else:
            print(f"\n{RED}Error: {e}{RESET}")
        sys.exit(1)

    # Guardar resultado si se especificó
    if args.output and result:
        output_path = Path(args.output)
        output_path.write_text(result, encoding="utf-8")
        print(f"\n{GREEN}✓  Resultado guardado en: {args.output}{RESET}")


if __name__ == "__main__":
    main()
