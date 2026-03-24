#!/usr/bin/env python3
"""
Agente Optimizador de Queries Informix
========================================
Analiza consultas SQL Informix pesadas y genera versiones optimizadas
que retornan exactamente los mismos resultados.

Uso:
    # Modo interactivo (pega el query en la terminal):
    python optimizer.py

    # Query directo por argumento:
    python optimizer.py "SELECT * FROM polizas WHERE ..."

    # Query desde archivo:
    python optimizer.py --file mi_query.sql

    # Esquema personalizado:
    python optimizer.py --schema /ruta/otro_esquema.sql "SELECT ..."

    # Sin streaming (espera respuesta completa):
    python optimizer.py --no-stream "SELECT ..."
"""

import argparse
import sys
from pathlib import Path

# Colores ANSI para la terminal
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_banner():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════════════╗
║      Agente Optimizador de Queries Informix          ║
║      Powered by Claude Opus 4.6                      ║
╚══════════════════════════════════════════════════════╝{RESET}
""")


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
        print(f"Error: No se encontró el archivo '{file_path}'")
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
        help="El query SQL a optimizar (entre comillas). Si se omite, se activa el modo interactivo.",
    )
    parser.add_argument(
        "--file", "-f",
        metavar="ARCHIVO.sql",
        help="Leer el query desde un archivo .sql",
    )
    parser.add_argument(
        "--schema", "-s",
        metavar="ESQUEMA.sql",
        help="Ruta al archivo de esquema SQL (por defecto: schemas/seguros.sql)",
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

    # Determinar el query a optimizar
    if args.file:
        query = read_query_from_file(args.file)
        print(f"{GREEN}Query cargado desde: {args.file}{RESET}\n")
    elif args.query:
        query = args.query.strip()
    else:
        query = read_query_interactive()

    if not query:
        print("Error: el query está vacío.")
        sys.exit(1)

    # Mostrar el query recibido
    print(f"{CYAN}{BOLD}━━━ QUERY ORIGINAL ━━━{RESET}")
    print(query)
    print(f"{CYAN}{'━' * 40}{RESET}\n")

    # Importar aquí para evitar error si falta la key antes de mostrar ayuda
    try:
        from agent.core import optimize_query
    except ImportError as e:
        print(f"Error al importar el agente: {e}")
        print("Asegúrate de tener instaladas las dependencias: pip install -r requirements.txt")
        sys.exit(1)

    schema_path = Path(args.schema) if args.schema else None

    print(f"{CYAN}{BOLD}━━━ ANÁLISIS Y OPTIMIZACIÓN ━━━{RESET}\n")

    try:
        result = optimize_query(
            query=query,
            schema_path=schema_path,
            stream_output=not args.no_stream,
        )
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            print(f"\nError de autenticación: configura tu API key de Anthropic.")
            print("  En Windows (PowerShell): $env:ANTHROPIC_API_KEY = 'tu-api-key'")
            print("  En Linux/Mac:            export ANTHROPIC_API_KEY='tu-api-key'")
        else:
            print(f"\nError al ejecutar el agente: {e}")
        sys.exit(1)

    # Guardar resultado en archivo si se especificó
    if args.output and result:
        output_path = Path(args.output)
        output_path.write_text(result, encoding="utf-8")
        print(f"\n{GREEN}Resultado guardado en: {args.output}{RESET}")


if __name__ == "__main__":
    main()
