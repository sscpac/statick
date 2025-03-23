FROM ubuntu:24.04

LABEL "name"="Statick DevContainer"
LABEL "version"="0.0"
LABEL "repository"="https://github.com/triboelectric/statick"
LABEL "homepage"="https://github.com/triboelectric/statick"
LABEL "maintainer"="Thomas Denewiler <tdenewiler@gmail.com>"

USER root

ENV DEBIAN_FRONTEND=noninteractive

# Developer Packages
RUN apt-get update && apt-get install --no-install-recommends -y \
    bash-completion \
    ca-certificates \
    gitk \
    less \
    vim && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Version pinning may be added in the future, but ignore for now.
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cccc \
    chktex \
    clang \
    clang-18 \
    clang-format \
    clang-format-18 \
    clang-tidy \
    clang-tidy-18 \
    cmake \
    cppcheck \
    curl \
    file \
    findbugs \
    flawfinder \
    git \
    lacheck \
    libomp-dev \
    libpcre3-dev \
    libperl-critic-perl \
    libxml2 \
    libxml2-utils \
    maven \
    python3-pip \
    python3-venv \
    shellcheck \
    uncrustify \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install hadolint executable from their Docker image.
COPY --from=hadolint/hadolint:2.12.0-debian /bin/hadolint /usr/bin/hadolint

# Install uv for virtual environment
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Version pinning may be added in the future, but ignore for now.
# hadolint ignore=DL3008,DL3016
RUN curl -sL https://deb.nodesource.com/setup_lts.x -o nodesource_setup.sh && \
    bash nodesource_setup.sh && \
    apt-get update && apt-get install -y --no-install-recommends nodejs && rm -rf /var/lib/apt/lists/* && \
    npm config set prefix -g /usr && \
    npm install -g dockerfilelint && \
    npm install -g dockerfile_lint && \
    npm install -g htmllint-cli && \
    npm install -g markdownlint-cli && \
    npm install -g npm-groovy-lint && \
    # needed for stylelint to process html
    npm install -g postcss-html && \
    npm install -g prettier && \
    npm install -g stylelint && \
    npm install -g stylelint-config-standard && \
    npm install -g write-good && \
    npm install -g eslint && \
    # eslint plugins and configs should be installed locally
    # https://eslint.org/docs/user-guide/migrating-to-6.0.0#plugins-and-shareable-configs-are-no-longer-affected-by-eslints-location
    npm install --prefix $HOME/.node_modules eslint-plugin-html && \
    npm install --prefix $HOME/.node_modules eslint-plugin-prettier && \
    npm install --prefix $HOME/.node_modules eslint-config-prettier && \
    # View versions of installed packages
    npm list && \
    npm list --prefix $HOME/.node_modules && \
    npm list -g

ENV HOME=/root
WORKDIR ${HOME}

# Fancy prompt.
COPY .devcontainer/config/.git-prompt.sh ${HOME}/.git-prompt.sh
COPY .devcontainer/config/.bash_prompt ${HOME}/.bash_prompt
RUN echo ". ~/.git-prompt.sh" >> ${HOME}/.bashrc && \
    echo ". ~/.bash_prompt" >> ${HOME}/.bashrc && \
    wget https://raw.githubusercontent.com/git/git/master/contrib/completion/git-completion.bash -o ~/.git-completion.bash && \
    echo " \
    if [ -f ~/.git-completion.bash ]; then \
      . ~/.git-completion.bash \
    fi \
    " >> ${HOME}/.bashrc

WORKDIR /opt