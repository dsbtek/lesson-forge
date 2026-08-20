# LessonForge web image (Next.js, dev mode).
# A production multi-stage build (next build/start) is a later-phase follow-up.
FROM node:20-slim

WORKDIR /app

# Install dependencies first for better layer caching. package-lock.json is
# optional on first run; npm generates it inside the container.
COPY apps/web/package.json ./
COPY apps/web/package-lock.json* ./
RUN npm install

# Application source (overlaid by a bind-mount in dev compose; node_modules is
# preserved via an anonymous volume declared in docker-compose.yml).
COPY apps/web/ ./

EXPOSE 3000
CMD ["npm", "run", "dev"]
