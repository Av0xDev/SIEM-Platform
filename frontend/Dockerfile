FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 3001
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3001 || exit 1
CMD ["serve", "-s", "dist", "-l", "3001"]