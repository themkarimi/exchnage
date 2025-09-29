FROM python:3.10.0-slim-bullseye as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app


# Create non-root user early
RUN adduser --system --no-create-home --uid 1001 nonroot

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install -r requirements.txt

COPY --chown=nonroot:nogroup . .

USER nonroot

# Add the missing CMD instruction
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--chdir", "Exchange", "Exchange.wsgi:application"]




