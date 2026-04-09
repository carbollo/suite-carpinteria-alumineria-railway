# Suite de Herramientas para Carpinteria y Alumineria

Aplicacion web lista para deploy en Railway con:

- Gestion de clientes
- Gestion de proyectos (carpinteria y alumineria)
- Presupuestos con calculo automatico de margen
- Gestion de tareas por proyecto
- API REST + interfaz web simple

## Stack

- FastAPI
- SQLAlchemy
- SQLite local (y PostgreSQL en Railway via `DATABASE_URL`)
- HTML/CSS/JS vanilla

## Ejecutar local

1. Crear entorno virtual
2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar:

```bash
uvicorn app.main:app --reload
```

4. Abrir `http://127.0.0.1:8000`

## Deploy en Railway

1. Crear nuevo proyecto en Railway.
2. Conectar este repositorio de GitHub.
3. (Opcional recomendado) Agregar un plugin PostgreSQL en Railway.
4. Definir variable `DATABASE_URL` (Railway lo hace automaticamente al crear PostgreSQL).
5. Deploy: Railway detecta `Procfile` y ejecuta:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Endpoints principales

- `GET /health`
- `GET/POST /api/clientes`
- `GET/POST /api/proyectos`
- `GET/POST /api/presupuestos`
- `GET/POST /api/tareas`
