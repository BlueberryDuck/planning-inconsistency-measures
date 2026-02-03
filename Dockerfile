FROM python:3.12-slim

WORKDIR /workspace
COPY pyproject.toml .
COPY planning_measures/ planning_measures/
COPY encodings/ encodings/

RUN pip install --no-cache-dir -e ".[dev]"

CMD ["/bin/bash"]
