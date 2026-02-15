FROM oven/bun:alpine AS development

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install

COPY . .

EXPOSE 3000

CMD ["bun", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

FROM oven/bun:alpine AS builder

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .

RUN bun run build

FROM nginx:alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
