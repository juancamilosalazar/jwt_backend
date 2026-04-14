# CLAUDE.md — CODIT Backend

## Regla principal: Leer requerimientos antes de programar

**OBLIGATORIO:** Antes de escribir, modificar o refactorizar cualquier codigo en este proyecto, debes leer todos los archivos dentro de la carpeta:

```
requerimientos_arquitectura_hus/
```

Esta carpeta contiene las historias de usuario (HUs), decisiones de arquitectura, convenciones de codigo y restricciones del proyecto. Sin leerlos primero, no se puede garantizar que los cambios sean coherentes con el diseno del sistema.

### Cuando aplica esta regla

- Al implementar un nuevo endpoint o router
- Al modificar modelos, schemas o la base de datos
- Al agregar o cambiar logica de autenticacion/autorizacion
- Al crear o modificar cualquier archivo `.py` del proyecto
- Al instalar o actualizar dependencias en `requirements.txt`
- Ante cualquier duda sobre como debe comportarse una funcionalidad

### Como leer los requerimientos

1. Listar todos los archivos en `requerimientos_arquitectura_hus/`
2. Leer cada archivo relevante segun la tarea a realizar
3. Aplicar las convenciones y restricciones encontradas antes de escribir codigo

---

## Stack del proyecto

| Componente       | Tecnologia                        |
|------------------|-----------------------------------|
| Framework        | FastAPI                           |
| ORM              | SQLAlchemy 2.x                    |
| Base de datos    | PostgreSQL (psycopg2-binary)      |
| Autenticacion    | JWT con python-jose + passlib     |
| Servidor         | Uvicorn                           |
| Variables de env | python-dotenv (.env)              |

## Estructura del proyecto

```
Backend/
├── main.py                         # Punto de entrada, configuracion CORS y routers
├── database.py                     # Conexion SQLAlchemy, engine y sesion
├── models.py                       # Modelos ORM (tablas de la DB)
├── schemas.py                      # Schemas Pydantic (request/response)
├── auth.py                         # Logica de JWT y hashing de contrasenas
├── requirements.txt                # Dependencias del proyecto
├── routers/
│   ├── auth.py                     # Endpoints de autenticacion
│   ├── users.py                    # Endpoints de usuarios
│   └── test.py                     # Endpoints de prueba
└── requerimientos_arquitectura_hus/  # <-- LEER SIEMPRE ANTES DE PROGRAMAR
```

## Convenciones generales

- Los routers van en `routers/` y se registran en `main.py`
- Los modelos ORM van en `models.py`; los schemas Pydantic en `schemas.py`
- La logica de autenticacion y tokens va en `auth.py`
- No exponer datos sensibles (contrasenas, tokens) en los schemas de respuesta
- Usar dependencias de FastAPI (`Depends`) para inyectar la sesion de DB y el usuario actual
- El frontend corre en `http://localhost:4200` — CORS ya esta configurado para ese origen

## Variables de entorno

El archivo `.env` (no versionado) debe contener las credenciales de la base de datos y la clave secreta JWT. Consulta el archivo antes de asumir valores por defecto.
