FROM python:3.11

# Install Node.js (>= 18) and necessary tools
RUN apt-get update \
  && apt-get install -y --no-install-recommends nodejs npm \
  && rm -rf /var/lib/apt/lists/*

# Copy uv from the official uv image
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Copy dependency descriptor files first to leverage Docker cache
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml backend/uv.lock ./backend/

# Install dependencies (Node + Python)
RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && uv sync --frozen

# Copy project source code
COPY . .

# CAMEL-AI tool-call ordering fix for MiniMax compatibility.
# Drops the patch into the venv's site-packages and registers a .pth file
# so it auto-loads in any Python subprocess that uses the venv (including
# the OASIS simulation engine spawned by the backend).
RUN cp /app/camel_tool_call_fix.py /app/backend/.venv/lib/python3.11/site-packages/camel_tool_call_fix.py \
 && echo "import camel_tool_call_fix" > /app/backend/.venv/lib/python3.11/site-packages/zzz_camel_tool_call_fix.pth

EXPOSE 3000 5001

# Start both frontend and backend simultaneously (development mode)
CMD ["npm", "run", "dev"]