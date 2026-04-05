FROM node:22-alpine AS build
WORKDIR /app
COPY site/package*.json ./
RUN npm ci
COPY site/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN printf 'server {\n  listen 80;\n  server_name _;\n  root /usr/share/nginx/html;\n  index index.html;\n  server_tokens off;\n  gzip on;\n  gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;\n  location / {\n    try_files $uri $uri/ /index.html;\n  }\n  add_header X-Frame-Options "SAMEORIGIN" always;\n  add_header X-Content-Type-Options "nosniff" always;\n  add_header Referrer-Policy "strict-origin-when-cross-origin" always;\n}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
