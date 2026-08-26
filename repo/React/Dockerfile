# --- Etapa 1: build de la app React con Vite ---
FROM node:22-alpine AS build

WORKDIR /app

# Habilitar pnpm (el proyecto usa pnpm-lock.yaml)
RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

# La URL del backend se puede inyectar en build-time
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN pnpm run build

# --- Etapa 2: servir los archivos estáticos con nginx ---
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
