# Esquema de la Base de Datos Informix

Coloca aquí los archivos `.sql` con los DDLs de tus tablas.
El agente cargará **todos** los archivos `.sql` de esta carpeta automáticamente.

## Cómo exportar desde Aqua Data Studio

1. Conectarse a la base de datos en Aqua Data Studio
2. Click derecho sobre la base de datos → **Generate DDL**
3. Seleccionar todas las tablas → exportar como `.sql`
4. Copiar el archivo generado a esta carpeta

## Qué debe incluir el archivo

- `CREATE TABLE` con todos los tipos de columnas
- `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `NOT NULL`
- `CREATE INDEX` — **importante** para que el agente detecte qué índices existen

## Ejemplo

```sql
CREATE TABLE polizas (
    id          SERIAL        NOT NULL,
    numero      CHAR(20)      NOT NULL,
    estado      CHAR(1)       NOT NULL,
    cliente_id  INTEGER       NOT NULL,
    fecha_ini   DATE          NOT NULL,
    fecha_fin   DATE          NOT NULL,
    prima       DECIMAL(15,2) NOT NULL,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX idx_pol_numero  ON polizas(numero);
CREATE INDEX        idx_pol_cliente ON polizas(cliente_id, estado);

CREATE TABLE siniestros (
    id         SERIAL        NOT NULL,
    poliza_id  INTEGER       NOT NULL,
    fecha      DATE          NOT NULL,
    monto      DECIMAL(15,2),
    estado     CHAR(2),
    PRIMARY KEY (id),
    FOREIGN KEY (poliza_id) REFERENCES polizas(id)
);

CREATE INDEX idx_sin_poliza ON siniestros(poliza_id);
CREATE INDEX idx_sin_fecha  ON siniestros(fecha, estado);
```

## Múltiples archivos

Puedes dividir el esquema en varios archivos, por ejemplo:

```
db-esquema/
├── 01_tablas_maestras.sql
├── 02_polizas.sql
├── 03_siniestros.sql
└── 04_reportes.sql
```

El agente los carga en orden alfabético.
