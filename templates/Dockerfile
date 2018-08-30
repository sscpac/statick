FROM ubuntu:xenial
MAINTAINER SPAWAR

USER root

# Set up the locale
RUN apt-get update && apt-get install -y locales
RUN locale-gen en_US en_US.UTF-8
RUN update-locale LC_ALL=en_US.UTF-8

# Statick requirements

# packages available from apt
RUN apt-get update && apt-get install -y git wget build-essential cppcheck cmake pylint libxml2 python-yapsy libomp-dev bandit flawfinder python-pylint-django
# Python requirements
RUN apt-get update && apt-get install -y python-yapsy python-yaml flawfinder clang-tidy clang-format clang python-yapsy findbugs
RUN pip install --upgrade pip
RUN pip install yamllint cmakelint lizard flake8 flake8-blind-except flake8-builtins flake8-class-newline flake8-comprehensions flake8-docstrings flake8-import-order flake8-quotes 


# Jenkins user setup (keep this at the bottom)
RUN useradd -m jenkins -s /bin/bash
ENV JAVA_OPTS="-Xmx8292m"
USER jenkins
