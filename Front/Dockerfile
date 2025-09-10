FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json .
COPY pnpm-lock.yaml .

# Install pnpm and dependencies
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Copy source code (only what's needed)
COPY src/ ./src/
COPY public/ ./public/
COPY index.html .
COPY vite.config.ts .
COPY tsconfig.json .
COPY tsconfig.node.json .
COPY components.json .
COPY tailwind.config.ts .
COPY postcss.config.js .

# Build the application
RUN pnpm run build

# Install serve to serve static files
RUN npm install -g serve

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Serve the built application
CMD ["serve", "-s", "dist", "-l", "3000"]