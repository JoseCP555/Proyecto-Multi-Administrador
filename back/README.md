# Backend - Multi-Administrador

## Descripción

Este proyecto corresponde al backend del sistema **Multi-Administrador**, una aplicación web desarrollada para la administración de conjuntos residenciales y propiedades horizontales.

El backend fue desarrollado utilizando **FastAPI** y **PostgreSQL**, implementando una arquitectura basada en API REST para la gestión de usuarios, autenticación, recuperación de contraseñas y demás módulos del sistema.

---

# Tecnologías utilizadas

- Python 3.x
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Uvicorn

---

# Estructura del proyecto

```text
backend/
│
├── crud.py
├── database.py
├── email_config.py
├── main.py
├── models.py
├── schemas.py
├── requirements.txt
├── .env.example
└── README.md
```

---

# Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/JoseCP555/Proyecto-Multi-Administrador.git
```

## 2. Ingresar a la carpeta del backend

```bash
cd backend
```

## 3. Crear el entorno virtual

```bash
python -m venv .venv
```

## 4. Activar el entorno virtual

### Windows

```bash
.venv\Scripts\activate
```

### Linux / Mac

```bash
source .venv/bin/activate
```

## 5. Instalar las dependencias

```bash
pip install -r requirements.txt
```

---

# Variables de entorno

Crear un archivo `.env` utilizando como base el archivo:

```text
.env.example
```

Completar las variables necesarias para la conexión con la base de datos y el servicio de correo electrónico.

---

# Ejecución del servidor

Para iniciar el servidor de desarrollo ejecutar:

```bash
uvicorn main:app --reload
```

Por defecto el servidor se ejecutará en:

```
http://127.0.0.1:8000
```

---

# Funcionalidades implementadas

Actualmente el backend incluye funcionalidades como:

- Registro de usuarios.
- Inicio de sesión.
- Recuperación de contraseña mediante correo electrónico.
- Conexión con PostgreSQL.
- Operaciones CRUD sobre usuarios.
- Validación de datos mediante Pydantic.
- Configuración de CORS para comunicación con el frontend.

---

# Base de datos

El sistema utiliza **PostgreSQL** como gestor de base de datos.

La conexión se realiza mediante SQLAlchemy y las credenciales se configuran utilizando variables de entorno.

---

# Autoría

Proyecto desarrollado por:

- Isabella Olivares
- Sayeth Joseph Medina Bermúdez
- Kristian Andrei Luna Pérez
- Jose David Caicedo Padilla

Centro de Formación SENA

Programa: Tecnólogo en Análisis y Desarrollo de Software