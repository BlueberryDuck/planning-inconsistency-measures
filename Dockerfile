FROM python:3.12-slim

# Install plasp v3.1.1 from GitHub release
ADD https://github.com/potassco/plasp/releases/download/v3.1.1/plasp-3.1.1-linux-x86_64.tar.gz /tmp/
RUN tar xzf /tmp/plasp-3.1.1-linux-x86_64.tar.gz -C /tmp && \
    cp /tmp/plasp-3.1.1/plasp /usr/local/bin/plasp && \
    rm -rf /tmp/plasp-3.1.1*

WORKDIR /workspace
COPY pyproject.toml .
COPY planning_measures/ planning_measures/
COPY encodings/ encodings/

RUN pip install --no-cache-dir -e ".[dev]"

CMD ["/bin/bash"]
