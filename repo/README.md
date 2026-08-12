# Multi-Administrador

<p align="center">
  <img src="./images/logo.png" alt="Logo Multi-Administrador" width="220">
</p>

<p align="center">
Sistema web para la administración integral de conjuntos residenciales y propiedades horizontales.
</p>

---

# Descripción

**Multi-Administrador** es una plataforma web desarrollada como proyecto formativo del **Servicio Nacional de Aprendizaje (SENA)**, orientada a facilitar la gestión administrativa de conjuntos residenciales, edificios y propiedades horizontales.

La aplicación centraliza procesos administrativos, financieros y documentales mediante una arquitectura cliente-servidor, permitiendo administrar la información de residentes, inmuebles, pagos, mantenimientos, documentos y demás recursos asociados a una copropiedad.

---

# Objetivos del proyecto

## Objetivo general

Desarrollar una plataforma web que permita administrar de manera eficiente la información y los procesos internos de conjuntos residenciales.

## Objetivos específicos

* Gestionar usuarios y residentes.
* Administrar propiedades e inmuebles.
* Controlar la información financiera.
* Gestionar documentación administrativa.
* Registrar mantenimientos y solicitudes.
* Generar reportes administrativos.
* Facilitar la comunicación entre administradores y residentes.

---

# Integrantes

* Isabella Olivares
* Sayeth Joseph Medina Bermúdez
* Kristian Andrei Luna Pérez
* Jose David Caicedo Padilla

---

# Tecnologías utilizadas

## Frontend

* React
* TypeScript
* Vite
* React Router DOM
* PNPM

## Backend

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL
* Pydantic
* Uvicorn

## Base de datos

* PostgreSQL

## Herramientas de desarrollo

* Visual Studio Code
* Git
* GitHub
* pgAdmin 4
* SQLTools

---

# Arquitectura del proyecto

```text
Proyecto-Multi-Administrador
│
├── frontend/
│
├── backend/
│
├── docs/
│
├── images/
│
├── .gitignore
├── .env.example
└── README.md
```

---

# Módulos implementados

* Inicio de sesión
* Recuperación de contraseña
* Gestión de usuarios
* Gestión de residentes
* Gestión de propiedades
* Gestión financiera
* Gestión documental
* Mantenimiento
* Reportes
* Configuración

---

# Instalación

## Clonar el repositorio

```bash
git clone https://github.com/JoseCP555/Proyecto-Multi-Administrador.git
```

Ingresar al proyecto

```bash
cd Proyecto-Multi-Administrador
```

---

# Configuración del Frontend

Ingresar a la carpeta:

```bash
cd frontend
```

Instalar dependencias:

```bash
pnpm install
```

Ejecutar el proyecto:

```bash
pnpm dev
```

---

# Configuración del Backend

Ingresar a la carpeta:

```bash
cd backend
```

Crear entorno virtual:

```bash
python -m venv .venv
```

Activar entorno virtual.

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar el servidor:

```bash
uvicorn main:app --reload
```

---

# Variables de entorno

Para ejecutar correctamente el proyecto, crear un archivo `.env` utilizando como referencia el archivo:

```text
.env.example
```

Completar las variables correspondientes a:

* Base de datos.
* Claves secretas.
* Configuración SMTP.
* Configuración del servidor.

---

# Base de datos

El proyecto utiliza PostgreSQL como gestor de base de datos.

La estructura de la base de datos fue diseñada para soportar la administración de:

* Usuarios
* Roles
* Residentes
* Propiedades
* Documentos
* Finanzas

---

# Documentación

La documentación técnica y funcional del proyecto se encuentra organizada dentro de la carpeta:

```text
docs/
```

Incluye:

* Requisitos funcionales
* Requisitos no funcionales
* Restricciones
* Historias de usuario
* Reglas de negocio
* Endpoints
* Criterios de aceptación
* Flujo del sistema

---

# Capturas del sistema

## Inicio de sesión

  <img src="./images/Inicio Sesión.png" alt="Inicio Sesión Multi-Administrador" width="520">

---

## Dashboard

  <img src="./images/Dashboard.png" alt="Dashboard Multi-Administrador" width="520">

---

## Gestión de residentes

  <img src="./images/Gestión de Residentes.png" alt="Gestión de Residentes Multi-Administrador" width="520">


---

## Gestión Financiera

  <img src="./images/Gestión Financiera.png" alt="Gestión Financiera Multi-Administrador" width="520">


---

# Estado del proyecto

Actualmente el proyecto se encuentra en fase de desarrollo y continúa incorporando nuevas funcionalidades y mejoras.

---

# Buenas prácticas implementadas

* Arquitectura Cliente – Servidor.
* API REST.
* Gestión mediante Git y GitHub.
* Separación entre frontend y backend.
* Uso de variables de entorno.
* Documentación técnica.
* Control de versiones.

---

# Licencia

Proyecto desarrollado con fines académicos como evidencia del programa **Tecnólogo en Análisis y Desarrollo de Software** del **Servicio Nacional de Aprendizaje (SENA)**.

No está autorizado su uso comercial sin el consentimiento de los autores.

---

<p align="center">
Desarrollado por el equipo de Multi-Administrador • SENA 2026
</p>
