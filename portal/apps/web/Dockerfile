# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    npm ci --no-audit --no-fund --strict-ssl=true
COPY . .
RUN npm run build
FROM nginx:1.28-alpine
COPY --chmod=644 nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 8080
USER nginx
CMD ["nginx", "-g", "daemon off;"]

