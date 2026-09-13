FROM oven/bun:1.4.0-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/bun.lock ./
RUN bun install --frozen-lockfile
COPY frontend/ ./
RUN bun run build
FROM nginx:1.29-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY deploy/nginx/nginx.conf /etc/nginx/nginx.conf
COPY deploy/nginx/conf.d/operator.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
