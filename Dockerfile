FROM mambaorg/micromamba:1.5-jammy

# Install clingo and Python
RUN micromamba install -y -n base -c conda-forge \
    clingo=5.8.0 \
    python=3.12 \
    pip && \
    micromamba clean --all --yes

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN /opt/conda/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# Set working directory
WORKDIR /workspace

# Default to bash for interactive use
CMD ["/bin/bash"]
