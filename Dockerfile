FROM searxng/searxng@sha256:4d7ed8b7035ecf827bd901ba6d32f5c32d8119bc09bb3cdafeb0ce58f1b951c1

LABEL art.ayeque.searxng.upstream-version="2026.3.29+7ac4ff39f" \
      art.ayeque.searxng.upstream-revision="7ac4ff39fee4cdde223dbab6a83af9c26b56366e" \
      art.ayeque.searxng.upstream-digest="sha256:4d7ed8b7035ecf827bd901ba6d32f5c32d8119bc09bb3cdafeb0ce58f1b951c1" \
      art.ayeque.theme.revision="aya29.1" \
      org.opencontainers.image.source="https://github.com/dinozyavier/ayeque-searxng" \
      org.opencontainers.image.licenses="AGPL-3.0-only" \
      org.opencontainers.image.version="2026.3.29-aya29.1"

COPY ayeque.css /usr/local/searxng/searx/static/themes/simple/ayeque.css
COPY ayeque-logo.webp /usr/local/searxng/searx/static/themes/simple/img/ayeque-logo.webp
COPY favicon.png /usr/local/searxng/searx/static/themes/simple/img/favicon.png
COPY 192.png /usr/local/searxng/searx/static/themes/simple/img/192.png
COPY 512.png /usr/local/searxng/searx/static/themes/simple/img/512.png
COPY install_theme.py /tmp/install_ayeque_theme.py

RUN /usr/local/searxng/.venv/bin/python /tmp/install_ayeque_theme.py \
    && chmod 0644 \
        /usr/local/searxng/searx/static/themes/simple/ayeque.css \
        /usr/local/searxng/searx/static/themes/simple/img/ayeque-logo.webp \
        /usr/local/searxng/searx/static/themes/simple/img/favicon.png \
        /usr/local/searxng/searx/static/themes/simple/img/192.png \
        /usr/local/searxng/searx/static/themes/simple/img/512.png \
    && rm /tmp/install_ayeque_theme.py
