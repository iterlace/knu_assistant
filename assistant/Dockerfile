FROM ubuntu:20.04

RUN apt update -y && apt upgrade -y && \
    apt install -y apt-utils software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt install -y python3.9 python3-pip
RUN python3.9 -m pip install poetry==1.1.10
RUN ln -s $(which python3.9) /bin/python

WORKDIR /opt/assistant
ENV PYTHONPATH=$PYTHONPATH:/opt/assistant

COPY src/poetry.lock src/pyproject.toml /opt/assistant/

RUN python3.9 -m poetry install --no-dev --no-root;

COPY src/ /opt/assistant/

ARG DEBUG=false
RUN bash -c "\
cd /opt/assistant/; \
if [ $DEBUG == 'true' ] ; \
    then python3.9 -m poetry install; \
    else python3.9 -m poetry install --no-dev ; \
fi"

