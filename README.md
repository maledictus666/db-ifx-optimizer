# Agente Optimizador de Queries Informix

Agente de inteligencia artificial que analiza consultas SQL Informix pesadas y genera versiones optimizadas que retornan exactamente los mismos resultados.

## Características

- **Análisis estático** — no requiere conexión directa a la base de datos
- **Conocimiento Informix específico** — hints del optimizador, sintaxis `FIRST/SKIP`, CTEs, índices compuestos
- **Detección automática** de patrones problemáticos:
  - Subconsultas correlacionadas
  - Funciones en columnas indexadas
  - JOINs múltiples sin índices
  - Agregaciones masivas sin filtros previos
  - `SELECT *` innecesarios
  - `NOT IN` con posibles NULLs
- **Checklist de validación** — pasos concretos para verificar que el resultado sea idéntico
- **Índices recomendados** — DDLs listos para ejecutar en Informix

## Requisitos

- Python 3.10+
- API key de Anthropic ([obtener aquí](https://console.anthropic.com))

## Instalación

```bash
pip install -r requirements.txt
```

Configura tu API key:

```powershell
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY = "tu-api-key"
```

```bash
# Linux / Mac
export ANTHROPIC_API_KEY="tu-api-key"
```

## Configurar el esquema

Coloca tus archivos `.sql` (exportados desde Aqua Data Studio) en la carpeta `db-esquema/`.
El agente carga **todos** los `.sql` que encuentre ahí automáticamente.

```
db-esquema/
├── polizas.sql        <- CREATE TABLE + índices
├── siniestros.sql
└── maestras.sql
```

Ver `db-esquema/README.md` para instrucciones de exportación desde Aqua Data Studio.

## Uso

### Modo interactivo (pegar el query en la terminal)

```bash
python optimizer.py
```

### Query directo por argumento

```bash
python optimizer.py "SELECT p.numero, SUM(s.monto) FROM polizas p, siniestros s WHERE s.poliza_id = p.id GROUP BY p.numero"
```

### Desde archivo .sql

```bash
python optimizer.py --file mi_query_pesado.sql
```

### Guardar resultado en archivo

```bash
python optimizer.py --file query.sql --output resultado.md
```

### Con carpeta de esquema personalizada

```bash
python optimizer.py --db /ruta/a/mis-esquemas/ --file query.sql
```

## Estructura del proyecto

```
db-ifx-optimizer/
├── optimizer.py          # CLI principal
├── requirements.txt      # Dependencias Python
├── agent/
│   ├── __init__.py
│   ├── core.py           # Lógica de optimización + llamada a Claude
│   └── prompts.py        # System prompt con conocimiento Informix
└── db-esquema/
    ├── README.md         # Instrucciones de exportación desde Aqua Data Studio
    └── *.sql             # Tus archivos de esquema (agregar manualmente)
```

## Ejemplo de salida

El agente genera un análisis estructurado con:

1. **DIAGNÓSTICO** — problemas de rendimiento detectados en el query original
2. **QUERY OPTIMIZADO** — el SQL listo para ejecutar en Informix
3. **CAMBIOS REALIZADOS** — explicación de cada modificación
4. **CHECKLIST DE VALIDACIÓN** — queries de verificación para confirmar equivalencia
5. **ÍNDICES RECOMENDADOS** — DDLs de índices que mejorarían el rendimiento
6. **ADVERTENCIAS** — casos edge o suposiciones del análisis estático
