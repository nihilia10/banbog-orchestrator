# BanBog Orchestrator: Mi Llave 🚀

BanBog Orchestrator es un sistema de IA multi-agente diseñado para orquestar consultas a través de diferentes fuentes de datos (SQL y Vector Stores) para el análisis de documentos financieros y reseñas bancarias.

## 🎯 Objetivo

El objetivo principal de este proyecto es proporcionar una interfaz inteligente que pueda responder preguntas complejas sobre:
- **Productos Bancarios**: Información extraída de catálogos en formato PDF.
- **Reseñas de Clientes**: Datos estructurados sobre experiencias de usuarios en diferentes sucursales.
- **Documentación Técnica (BRE-B)**: Consultas sobre normativas y guías técnicas específicas.

El sistema utiliza un **Router Agent** para identificar la intención del usuario y dirigir la consulta al agente especializado correspondiente (RAG o SQL).

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web moderno y rápido para construir la API.
- **LangChain**: Framework para el desarrollo de aplicaciones impulsadas por modelos de lenguaje.
- **OpenAI**: Modelos de lenguaje avanzados (GPT-4.1-nano) para el procesamiento de lenguaje natural.
- **FAISS**: Biblioteca para búsqueda de similitud eficiente en vectores densos.
- **SQLite**: Motor de base de datos relacional para el almacenamiento de reseñas.

### Frontend
- **Next.js**: Framework de React para la interfaz de usuario.
- **Tailwind CSS**: Framework de CSS para un diseño moderno y responsivo.
- **TypeScript**: Para un desarrollo más robusto y seguro.

## 📂 Estructura del Proyecto

```text
.
├── api/                # Endpoints de la API (Vercel Serverless Functions)
├── frontend/           # Aplicación Next.js (Interfaz de usuario)
├── src/                # Lógica del núcleo y Agentes
│   ├── router_agent.py      # Clasifica la intención del usuario
│   ├── orchestrator_agent.py # Coordina la interacción entre agentes
│   ├── rag.py               # Agente para recuperación-generación (PDFs)
│   ├── sql_agent.py         # Agente para consultas a la base de datos SQL
│   └── build_vector_db.py   # Script para procesar documentos e indexarlos
├── faiss_index/        # Almacenamiento del índice vectorial
├── bank_reviews.db     # Base de datos SQLite
├── dev.sh              # Script para ejecución simultánea (Local)
└── vercel.json         # Configuración para despliegue en Vercel
```

## 🚀 Cómo Ejecutar el Proyecto

### 1. Configuración de Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto con las siguientes claves:
```env
OPENAI_API_KEY=tu_api_key_aqui
```

### 2. Ejecución Local (Script de Desarrollo)
La forma más sencilla de iniciar todo el sistema es usando el script `dev.sh`:
```bash
chmod +x dev.sh
./dev.sh
```

### 3. Ejecución Manual

#### Backend
```bash
# Opción 1: Interfaz de chat en consola
python main.py

# Opción 2: Servidor API
uvicorn api.index:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🌐 Despliegue

Este proyecto está configurado para ser desplegado en **Vercel**. La configuración se encuentra en el archivo `vercel.json`, permitiendo que tanto el frontend de Next.js como el backend de FastAPI coexistan en la misma plataforma.

---
*Desarrollado con ❤️ para la gestión inteligente de datos financieros.*
