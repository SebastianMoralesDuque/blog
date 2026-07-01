# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# Umami analytics (hardcoded for production)
ENV UMAMI_WEBSITE_ID=6626ec48-ab22-4b2c-a57b-b047721d9263
ENV UMAMI_SCRIPT_URL=https://analytics.sebastianmorales.sbs/script.js

RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
