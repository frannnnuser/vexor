# Vexor — Plataforma de Prediccion Binaria con ML

Vexor es una plataforma web de prediccion binaria con Machine Learning disenada para funcionar con cualquier tipo de dataset. El usuario sube su propio dataset, elige la columna objetivo, entrena el modelo y obtiene predicciones individuales o masivas.

---

## Stack Tecnologico

| Capa | Tecnologia |
|---|---|
| Backend | Python 3.12, FastAPI |
| Validacion | Pydantic v2 |
| ORM | SQLModel |
| Auth | Supabase Auth (JWT) |
| Base de datos | Supabase Postgres |
| ML | scikit-learn, pandas, numpy |
| Frontend | Bootstrap 5.3, Bootstrap Icons, Chart.js |
| Despliegue | Railway + Supabase |

---

## Estructura del Proyecto
vexor/
├── main.py
├── config.py
├── dependencies.py
├── models.py
├── ml_engine.py
├── routers/
│   ├── auth.py
│   ├── dashboard.py
│   ├── predict.py
│   ├── training.py
│   ├── history.py
│   └── audit.py
├── static/css/style.css
├── templates/
│   ├── base.html
│   ├── auth/
│   └── pages/
├── requirements.txt
└── .env.example
---

## Instalacion Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/vexor.git
cd vexor
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
# o
source venv/bin/activate      # Mac / Linux
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales de Supabase.

### 5. Ejecutar el servidor

```bash
uvicorn main:app --reload
```

Abre tu navegador en `http://localhost:8000`

---

## Variables de Entorno

| Variable | Descripcion |
|---|---|
| SUPABASE_URL | URL del proyecto en Supabase |
| SUPABASE_ANON_KEY | Clave publica de Supabase |
| SUPABASE_SERVICE_ROLE_KEY | Clave de servicio de Supabase |
| DATABASE_URL | URL de conexion a Postgres |
| SECRET_KEY | Clave secreta para JWT |
| ALGORITHM | Algoritmo JWT (HS256) |
| ACCESS_TOKEN_EXPIRE_MINUTES | Duracion del token en minutos |
| ENVIRONMENT | development o production |
| ALLOWED_ORIGINS | Origenes permitidos para CORS |
| MAX_UPLOAD_SIZE_MB | Tamano maximo de archivos subidos |
| MODEL_PATH | Ruta donde se guarda el modelo |

---

## Roles de Usuario

| Rol | Permisos |
|---|---|
| admin | Acceso total: entrenar, predecir, ver historial, audit log, eliminar |
| analyst | Predecir individualmente, masivamente y ver historial |

---

## ML Engine

- Acepta CSV, XLSX y XLS
- Detecta automaticamente columnas numericas y categoricas
- Descarta columnas con mas del 60% de valores nulos
- Pipeline: SimpleImputer + StandardScaler para numericas, SimpleImputer + OrdinalEncoder para categoricas
- Clasificador: LogisticRegression
- Split estratificado 80/20
- Persistencia del modelo con pickle
- Operaciones ML en executor para no bloquear el event loop

---

## Despliegue en Railway

1. Sube el proyecto a GitHub
2. Conecta el repositorio en Railway
3. Configura las variables de entorno en Railway
4. Railway detecta el `Procfile` y despliega automaticamente

---

## Licencia

MIT