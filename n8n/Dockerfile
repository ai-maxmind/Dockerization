ARG NODE_VERSION=18
ARG N8N_VERSION=latest
FROM --platform=$BUILDPLATFORM node:${NODE_VERSION}-bullseye AS build

LABEL org.opencontainers.image.source="https://github.com/ai-maxmind/Dockerization" \
      org.opencontainers.image.licenses="MIT" \
      maintainer="Hau Nguyen <haunt170@gmail.com>"

ARG BUILD_DATE
ARG VCS_REF

ENV NPM_CONFIG_UPDATE_NOTIFIER=false \
    NODE_ENV=production \
    unsafe-perm=false

WORKDIR /usr/src/app
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    ca-certificates \
    git \
 && rm -rf /var/lib/apt/lists/*
COPY package*.json pnpm-lock.yaml* ./
RUN if [ -f package-lock.json ]; then \
      echo "🔧 Using npm (package-lock.json found)"; \
      npm ci --no-audit --prefer-offline --omit=dev; \
    elif [ -f pnpm-lock.yaml ]; then \
      echo "🔧 Using pnpm (pnpm-lock.yaml found)"; \
      npm i -g pnpm@latest --no-audit --no-fund && pnpm install --frozen-lockfile --prod --offline || pnpm install --frozen-lockfile --prod; \
    else \
      echo "⚠️ No lockfile found — skipping local dependency install"; \
    fi

RUN npm i -g --no-audit --no-fund "n8n@${N8N_VERSION}"
RUN mkdir -p /artifacts/node_modules_global && \
    cp -a "$(npm root -g)" /artifacts/node_modules_global
FROM --platform=$TARGETPLATFORM debian:bullseye-slim AS runtime

ARG NODE_VERSION=18
ARG N8N_VERSION=latest
ARG APP_USER=n8n
ARG APP_UID=1001
ARG TZ="Asia/Ho_Chi_Minh"
ARG BUILD_DATE
ARG VCS_REF

LABEL org.opencontainers.image.title="n8n (custom optimized image)" \
      org.opencontainers.image.version="${N8N_VERSION}" \
      org.opencontainers.image.authors="Hau Nguyen <haunt170@gmail.com>" \
      org.opencontainers.image.created="${BUILD_DATE:-unknown}" \
      org.opencontainers.image.revision="${VCS_REF:-unknown}" \
      org.opencontainers.image.vendor="Personal"

ENV NODE_ENV=production \
    PATH=/home/${APP_USER}/.local/bin:/usr/local/bin:/usr/bin:/bin \
    N8N_PORT=5678 \
    N8N_EXECUTIONS_PROCESS=main \
    TZ=${TZ} \
    DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      tzdata \
      imagemagick \
      ffmpeg \
      tini \
 && rm -rf /var/lib/apt/lists/*

RUN groupadd -g ${APP_UID} ${APP_USER} || true && \
    useradd -u ${APP_UID} -g ${APP_UID} -m -s /bin/bash ${APP_USER} || true

WORKDIR /home/${APP_USER}

COPY --from=build /artifacts/node_modules_global /usr/local/lib/node_modules

RUN if [ -f /usr/local/lib/node_modules/n8n/bin/n8n ]; then \
      ln -sf /usr/local/lib/node_modules/n8n/bin/n8n /usr/local/bin/n8n; \
    fi

ENV N8N_USER_HOME=/home/${APP_USER}/.n8n

RUN mkdir -p ${N8N_USER_HOME} /data /tmp/n8n && chown -R ${APP_USER}:${APP_USER} /home/${APP_USER} /data /tmp/n8n

USER ${APP_USER}

EXPOSE ${N8N_PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fS --max-time 3 http://127.0.0.1:${N8N_PORT}/healthz || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["n8n", "start", "--tunnel"]
