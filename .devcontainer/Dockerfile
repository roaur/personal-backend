# Use the base Ubuntu image from dev containers
FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Install dependencies for pyenv and building Python
USER root
RUN apt-get update && apt-get install -y \
      build-essential \
      curl \
      libssl-dev \
      zlib1g-dev \
      libbz2-dev \
      libreadline-dev \
      libsqlite3-dev \
      wget \
      llvm \
      libncursesw5-dev \
      xz-utils \
      tk-dev \
      libxml2-dev \
      libxmlsec1-dev \
      libffi-dev \
      liblzma-dev \
      && rm -rf /var/lib/apt/lists/*

# Switch to the non-root user
USER vscode
ENV HOME /home/vscode

# Install pyenv in the non-root user's home directory
RUN curl https://pyenv.run | bash

# Set environment variables for the non-root user
ENV PYENV_ROOT="/home/vscode/.pyenv"
ENV PATH="${PYENV_ROOT}/bin:${PATH}"

# Shells need to load pyenv and pyenv-virtualenv
RUN echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc \
    && echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc \
    && echo 'eval "$(pyenv init -)"' >> ~/.bashrc \
    && echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

# Build Python 3.12.9
RUN pyenv install 3.12.9

# Set it as the global Python version
RUN pyenv global 3.12.9
