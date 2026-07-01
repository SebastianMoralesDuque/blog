# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# Accept build args for Umami
ARG UMAMI_WEBSITE_ID
ARG UMAMI_SCRIPT_URL
ENV UMAMI_WEBSITE_ID=$UMAMI_WEBSITE_ID
ENV UMAMI_SCRIPT_URL=$UMAMI_SCRIPT_URL

RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
