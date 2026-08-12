# Multi-Administrador — Frontend

Frontend en React + Vite + TypeScript.

## Requisitos

- Node.js 18+
- pnpm (`npm install -g pnpm` si no lo tienes)

## Instalación

```bash
pnpm install
```

## Variables de entorno

Copia `.env.example` a `.env` y ajusta según tu entorno:

```
VITE_API_URL=http://127.0.0.1:8000
```

`VITE_API_URL` debe apuntar al backend FastAPI (ver `../back/README.md`).

## Comandos

```bash
pnpm dev       # servidor de desarrollo
pnpm build     # type-check + build de producción
pnpm preview   # sirve el build de producción localmente
```
