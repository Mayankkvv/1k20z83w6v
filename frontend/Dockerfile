# ---- Stage 1: build the React app into plain HTML, CSS and JavaScript files ----
FROM node:22-slim AS build

WORKDIR /app

# Install packages first. This layer is cached until package.json or the lock file changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# The backend address is built into the website files, so it must be known at build time.
# The browser (not the container) calls this address, so it is the address of the published backend port.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ---- Stage 2: serve the built files with nginx ----
FROM nginx:stable-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/ || exit 1