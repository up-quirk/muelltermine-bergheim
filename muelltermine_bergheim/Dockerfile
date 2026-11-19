FROM python:3.12-slim-bookworm
ARG BUILD_ARCH
ARG BUILD_VERSION=0.3.1
LABEL io.hass.name="Mülltermine Bergheim" \
      io.hass.description="Bergheim waste calendar with PDF rule preview" \
      io.hass.type="addon" \
      io.hass.version="${BUILD_VERSION}" \
      io.hass.arch="${BUILD_ARCH}"
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TZ=Europe/Berlin
WORKDIR /opt/muelltermine
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY muelltermine ./muelltermine
COPY run.py ./run.py
EXPOSE 8098 8099
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8098/healthz', timeout=3)"
CMD ["python", "run.py"]
