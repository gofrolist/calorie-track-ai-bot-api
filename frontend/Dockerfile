FROM node:22-alpine AS development

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Expose ports for development
EXPOSE 3000 5173

# Default command for development (can be overridden in docker-compose)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

FROM nginx:alpine AS runtime

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
