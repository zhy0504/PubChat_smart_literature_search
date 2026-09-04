FROM nginx:1.27-alpine

COPY frontend/dist /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/snippets /etc/nginx/snippets

# The repository contains the built frontend but not its source tree. Make the
# published bundle use the same-origin reverse proxy instead of localhost.
RUN find /usr/share/nginx/html/assets -type f -name '*.js' -exec sed -i 's#http://localhost:8000##g' {} +
