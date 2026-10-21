FROM ghcr.io/astral-sh/uv@sha256:ae1ba4db410fbe1d9eaf16c51add8e7608b271ebbb69bd58a56e80384fd190aa AS uv

FROM searxng/searxng@sha256:5ed0323b5f5f8701264ef65e239a2bd83cb57098f2b971fa30bf79c06eeae271

LABEL art.ayeque.searxng.upstream-version="2026.10.19+81371861f" \
      art.ayeque.searxng.upstream-revision="81371861f67226091d1c4df2e3908a11d3b54eb9" \
      art.ayeque.searxng.upstream-digest="sha256:5ed0323b5f5f8701264ef65e239a2bd83cb57098f2b971fa30bf79c06eeae271" \
      art.ayeque.searxng.security-dependencies="certifi=2026.10.19" \
      art.ayeque.theme.revision="aya35" \
      org.opencontainers.image.source="https://github.com/dinozyavier/ayeque-searxng" \
      org.opencontainers.image.licenses="AGPL-3.0-only" \
      org.opencontainers.image.version="2026.10.19-aya35"

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
    && test "$(/usr/local/searxng/.venv/bin/python -c 'import certifi; print(certifi.__version__)')" = "2026.10.19" \
    && /usr/local/searxng/.venv/bin/python /tmp/install_ayeque_theme.py \
    && chmod 0644 \
        /usr/local/searxng/searx/static/themes/simple/ayeque.css \
        /usr/local/searxng/searx/static/themes/simple/img/ayeque-logo.webp \
        /usr/local/searxng/searx/static/themes/simple/img/favicon.png \
        /usr/local/searxng/searx/static/themes/simple/img/192.png \
        /usr/local/searxng/searx/static/themes/simple/img/512.png \
        /usr/local/searxng/searx/engines/kiwix.py \
    && rm /tmp/install_ayeque_theme.py /tmp/security-requirements.txt /tmp/uv
