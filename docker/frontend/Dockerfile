FROM node:latest

WORKDIR /www

COPY ../../frontend/entrypoint.sh /entrypoint.sh
COPY ../../frontend /
RUN npm install

ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]

ENV HOST 0.0.0.0