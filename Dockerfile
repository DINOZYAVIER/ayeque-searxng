FROM ghcr.io/astral-sh/uv@sha256:ae1ba4db410fbe1d9eaf16c51add8e7608b271ebbb69bd58a56e80384fd190aa AS uv

FROM searxng/searxng@sha256:4d7ed8b7035ecf827bd901ba6d32f5c32d8119bc09bb3cdafeb0ce58f1b951c1

LABEL art.ayeque.searxng.upstream-version="2026.3.29+7ac4ff39f" \
      art.ayeque.searxng.upstream-revision="7ac4ff39fee4cdde223dbab6a83af9c26b56366e" \
      art.ayeque.searxng.upstream-digest="sha256:4d7ed8b7035ecf827bd901ba6d32f5c32d8119bc09bb3cdafeb0ce58f1b951c1" \
      art.ayeque.searxng.security-dependencies="granian=2.7.4,lxml=6.1.0,urllib3=2.7.0" \
      art.ayeque.theme.revision="aya34.1" \
      org.opencontainers.image.source="https://github.com/dinozyavier/ayeque-searxng" \
      org.opencontainers.image.licenses="AGPL-3.0-only" \
      org.opencontainers.image.version="2026.3.29-aya34.1"

COPY ayeque.css /usr/local/searxng/searx/static/themes/simple/ayeque.css
COPY ayeque-logo.webp /usr/local/searxng/searx/static/themes/simple/img/ayeque-logo.webp
COPY favicon.png /usr/local/searxng/searx/static/themes/simple/img/favicon.png
COPY 192.png /usr/local/searxng/searx/static/themes/simple/img/192.png
COPY 512.png /usr/local/searxng/searx/static/themes/simple/img/512.png
COPY install_theme.py /tmp/install_ayeque_theme.py
COPY kiwix.py /usr/local/searxng/searx/engines/kiwix.py
COPY security-requirements.txt /tmp/security-requirements.txt
COPY --from=uv /uv /tmp/uv

RUN /tmp/uv pip install --python /usr/local/searxng/.venv/bin/python \
        --no-deps --require-hashes --no-cache -r /tmp/security-requirements.txt \
    && test "$(/usr/local/searxng/.venv/bin/python -c 'import granian,lxml,urllib3; print(granian.__version__, lxml.__version__, urllib3.__version__)')" = "2.7.4 6.1.0 2.7.0" \
    && /usr/local/searxng/.venv/bin/python /tmp/install_ayeque_theme.py \
    && chmod 0644 \
        /usr/local/searxng/searx/static/themes/simple/ayeque.css \
        /usr/local/searxng/searx/static/themes/simple/img/ayeque-logo.webp \
        /usr/local/searxng/searx/static/themes/simple/img/favicon.png \
        /usr/local/searxng/searx/static/themes/simple/img/192.png \
        /usr/local/searxng/searx/static/themes/simple/img/512.png \
        /usr/local/searxng/searx/engines/kiwix.py \
    && rm /tmp/install_ayeque_theme.py /tmp/security-requirements.txt /tmp/uv
