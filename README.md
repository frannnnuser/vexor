<div align="center">

<img src="https://img.shields.io/badge/-%E2%AC%A1%20VEXOR-6366f1?style=for-the-badge&logoColor=white&labelColor=0a0a12" alt="Vexor" height="45">

### Plataforma de Prediccion de Churn con Machine Learning

*Detecta que clientes estan a punto de irse — antes de que sea tarde.*

<br>

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Supabase](https://img.shields.io/badge/Supabase-Auth%20%2B%20DB-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=flat-square&logo=bootstrap&logoColor=white)](https://getbootstrap.com)
[![Railway](https://img.shields.io/badge/Deploy-Railway-0B0D0E?style=flat-square&logo=railway&logoColor=white)](https://railway.app)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

<br>

<br>

</div>

---

## ¿Que es Vexor?

Vexor es una plataforma web de prediccion de churn (abandono de clientes) construida con Machine Learning. Permite a equipos de retención identificar con anticipacion que clientes tienen alta probabilidad de cancelar su servicio, para actuar antes de perderlos.

El flujo es simple: subes tu base de clientes, entrenas el modelo con un clic, y obtienes predicciones individuales o masivas con probabilidades de abandono en tiempo real.

---

## El Problema que Resuelve

```
Sin Vexor:                          Con Vexor:
─────────────────────────────────   ─────────────────────────────────
Cliente cancela                     Vexor detecta señal de riesgo
    ↓                                   ↓
Equipo se entera                    Equipo recibe alerta
    ↓                                   ↓
Ya es demasiado tarde                Equipo contacta al cliente
                                        ↓
                                    Cliente se queda
```

---

## Stack Tecnologico

| Capa | Tecnologia | Proposito |
|---|---|---|
| Backend | Python 3.12 + FastAPI | API REST + SSR |
| Validacion | Pydantic v2 | Validacion estricta de datos |
| ORM | SQLModel | Modelos y queries tipados |
| Auth | Supabase Auth + JWT | Autenticacion segura con roles |
| Base de datos | Supabase Postgres | Persistencia en la nube |
| ML | scikit-learn + pandas | Pipeline de prediccion |
| Frontend | Bootstrap 5.3 + Chart.js | UI responsive con graficos |
| Contenedor | Docker + docker-compose | Despliegue reproducible |
| Deploy | Railway | CI/CD desde GitHub |

---

## Funcionalidades

### Machine Learning
- Pipeline automatico: deteccion de columnas numericas y categoricas
- Preprocesamiento: `SimpleImputer` + `StandardScaler` + `OrdinalEncoder`
- Clasificador: `LogisticRegression` con split estratificado 80/20
- Metricas: Accuracy, F1, Precision, Recall
- Persistencia del modelo con pickle
- Operaciones ML asincronas con `run_in_executor`

### Predicciones
- **Individual** — ingresa datos de un cliente y obtiene probabilidad de churn
- **Masiva** — sube CSV o Excel con toda tu base de clientes
- Historial completo con busqueda, filtros y paginacion
- Exportacion a CSV con un clic

### Dashboard
- Contadores animados en tiempo real
- Grafico de tendencia de predicciones (30 dias)
- Distribucion de probabilidades (histograma)
- Positivos vs Negativos (donut chart)
- Matriz de confusion visual con tooltips
- Radar chart de metricas del modelo
- Gauge de tasa de churn
- Indicador de confianza del modelo

### Autenticacion y Roles
- **Admin** — entrenar modelos, ver audit log, eliminar predicciones, gestionar modelos
- **Analyst** — predecir individualmente, masivamente y ver historial

### Seguridad
- JWT en cookies HTTP-only
- Rate limiting con slowapi
- Validacion estricta de archivos subidos
- Headers de seguridad HTTP
- Sin queries SQL raw, todo via SQLModel
- Variables sensibles en `.env`

---

## Estructura del Proyecto

```
vexor/
├── main.py                  # Entry point, middlewares, routers
├── config.py                # Settings con pydantic-settings
├── dependencies.py          # Auth dependencies (JWT, roles)
├── models.py                # SQLModel + Pydantic schemas
├── ml_engine.py             # PredictionEngine (pipeline ML)
├── routers/
│   ├── auth.py              # Login, logout, change password
│   ├── dashboard.py         # Stats, graficos, metricas
│   ├── predict.py           # Prediccion individual y masiva
│   ├── training.py          # Entrenamiento y historial de modelos
│   ├── history.py           # Historial de predicciones
│   └── audit.py             # Audit log (solo admin)
├── static/css/style.css     # Estilos custom (dark/light mode)
├── templates/
│   ├── base.html            # Layout base con sidebar
│   ├── auth/                # Login, change password
│   └── pages/               # Dashboard, predict, history, etc.
├── Dockerfile               # Imagen Docker
├── docker-compose.yml       # Compose para desarrollo local
├── requirements.txt
├── Procfile                 # Railway deploy
└── .env.example
```

---

## Instalacion Local

### Con Docker (recomendado)

```bash
git clone https://github.com/tu-usuario/vexor.git
cd vexor
cp .env.example .env
# Edita .env con tus credenciales de Supabase
docker-compose up --build
```

Abre `http://localhost:8000`

### Sin Docker

```bash
git clone https://github.com/tu-usuario/vexor.git
cd vexor
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env
# Edita .env con tus credenciales de Supabase
uvicorn main:app --reload
```

---

## Variables de Entorno

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu-anon-key
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key
DATABASE_URL=postgresql://postgres.xxxxx:password@aws-x-xx.pooler.supabase.com:6543/postgres
SECRET_KEY=genera-con-python-secrets
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENVIRONMENT=production
ALLOWED_ORIGINS=https://tu-dominio.railway.app
MAX_UPLOAD_SIZE_MB=10
MODEL_PATH=model.pkl
```

Genera tu `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Dataset de Ejemplo

Para entrenar el modelo necesitas un CSV con datos de clientes. Columnas sugeridas:

| Columna | Tipo | Descripcion |
|---|---|---|
| `meses_activo` | Numerico | Tiempo como cliente |
| `plan` | Categorico | basic, pro, enterprise |
| `pagos_fallidos` | Numerico | Intentos de cobro fallidos |
| `tickets_soporte` | Numerico | Solicitudes de soporte |
| `ultimo_login_dias` | Numerico | Dias desde ultimo acceso |
| `nps_score` | Numerico | Net Promoter Score |
| `churn` | **Binario** | **0 = se queda, 1 = cancela** |

La columna objetivo debe tener exactamente **2 valores unicos**.

---

## Despliegue en Railway

```bash
git init
git add .
git commit -m "feat: initial commit"
git remote add origin https://github.com/tu-usuario/vexor.git
git push -u origin main
```

1. Conecta el repo en [railway.app](https://railway.app)
2. Agrega las variables de entorno
3. Railway detecta el `Procfile` y despliega automaticamente

---

## Roles de Usuario

```
Admin                          Analyst
─────────────────────────────  ─────────────────────────────
✓ Entrenar modelos             ✓ Prediccion individual
✓ Ver historial de modelos     ✓ Prediccion masiva
✓ Activar / desactivar modelo  ✓ Ver historial
✓ Ver audit log                ✗ No puede entrenar
✓ Eliminar predicciones        ✗ No puede eliminar
✓ Exportar audit log           ✓ Exportar historial
```

---

## Por que este Proyecto

Vexor fue construido para demostrar capacidad full-stack real en un contexto de negocio concreto. No es un tutorial ni un CRUD basico. Integra autenticacion con roles, ML en produccion, UI profesional y despliegue real en la nube.

El churn es uno de los problemas mas comunes y costosos en empresas SaaS. Retener un cliente existente cuesta entre 5 y 7 veces menos que adquirir uno nuevo. Vexor ataca ese problema directamente.

---

## Licencia

MIT — libre para usar, modificar y distribuir.

---

<div align="center">

Construido con precision por **Franco Villegas**

[![GitHub](https://img.shields.io/badge/GitHub-frannnnuser-181717?style=flat-square&logo=github)](https://github.com/frannnnuser)

</div>