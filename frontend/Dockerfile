# ---------- Build ----------
FROM node:20-alpine AS build
WORKDIR /app

# Usamos npm + package-lock.json (ya está en el repo y está sincronizado).
# Antes se usaba pnpm con `--no-frozen-lockfile` y SIN copiar el lockfile:
# cada build resolvía versiones distintas y podía romper `tsc`/Vite.
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .

# Vacío por defecto -> el frontend usa rutas relativas /api y nginx las
# reenvía al backend. Si necesitas apuntar a la API directamente, define
# VITE_API_URL=https://tu-api  (y añade el origen a ALLOWED_ORIGINS).
ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ---------- Runtime (nginx) ----------
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
