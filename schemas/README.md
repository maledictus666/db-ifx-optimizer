# Esquemas de Base de Datos

## Instrucciones

Coloca aquí tu archivo `seguros.sql` con los esquemas de las tablas de tu base de datos Informix.

El agente lo cargará automáticamente al ejecutar cualquier optimización.

## Formato esperado

El archivo debe contener las definiciones `CREATE TABLE` de tus tablas, incluyendo:
- Definición de columnas con sus tipos de datos
- Restricciones (PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL)
- Índices creados sobre las tablas

### Ejemplo

```sql
CREATE TABLE polizas (
    id          SERIAL          NOT NULL,
    numero      CHAR(20)        NOT NULL,
    estado      CHAR(1)         NOT NULL,
    ramo_id     INTEGER         NOT NULL,
    cliente_id  INTEGER         NOT NULL,
    fecha_inicio DATE           NOT NULL,
    fecha_fin   DATE            NOT NULL,
    prima       DECIMAL(15,2)   NOT NULL,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX idx_polizas_numero ON polizas(numero);
CREATE INDEX idx_polizas_estado ON polizas(estado);
CREATE INDEX idx_polizas_cliente ON polizas(cliente_id, estado);

CREATE TABLE siniestros (
    id          SERIAL          NOT NULL,
    poliza_id   INTEGER         NOT NULL,
    fecha       DATE            NOT NULL,
    monto       DECIMAL(15,2),
    estado      CHAR(2),
    PRIMARY KEY (id),
    FOREIGN KEY (poliza_id) REFERENCES polizas(id)
);

CREATE INDEX idx_siniestros_poliza ON siniestros(poliza_id);
```

## Notas

- El archivo es opcional: el agente puede optimizar queries sin esquema, pero con el esquema el análisis es más preciso
- Puedes exportar los DDLs directamente desde Aqua Data Studio
- Si tienes múltiples esquemas, puedes concatenarlos en un solo archivo
