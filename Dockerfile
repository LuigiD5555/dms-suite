FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LD_LIBRARY_PATH="/usr/lib/libreoffice/lib:$LD_LIBRARY_PATH"

WORKDIR /app

# Only system dependencies required for production:
# - build-essential/gcc/pkg-config/default-libmysqlclient-dev/libmariadb-dev for mysqlclient
# - LibreOffice for conversions and reports
#
# libgirepository, libcairo, graphviz, and libgraphviz-dev were removed because
# they belonged to gaphor/pygraphviz, development tools that broke the build.
COPY requirements.txt /app/
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    libmariadb-dev \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "EnterpriseApp.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
