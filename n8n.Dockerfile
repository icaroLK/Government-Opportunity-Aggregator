# n8n.Dockerfile
FROM n8nio/n8n:latest

USER root
RUN apk add --no-cache docker-cli

# mantém entrypoint padrão
