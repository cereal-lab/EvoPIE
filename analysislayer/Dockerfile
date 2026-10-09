FROM ubuntu:20.04

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y && \
    apt-get upgrade -y
RUN apt-get install -y python3 python3-pip
RUN apt-get install -y sqlite3 git
RUN apt-get install -y nmap
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata
RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

ENV TZ="America/New_York"

WORKDIR /app
ARG EVOPIE_GIT_REF=master
RUN echo "Building EvoPIE from ${EVOPIE_GIT_REF}"
RUN git clone https://github.com/cereal-lab/EvoPIE.git .
RUN git checkout "${EVOPIE_GIT_REF}"

RUN uv sync --frozen --no-dev
#RUN uv run --frozen flask DB-reboot

ENV EVOPIE_UPDATER_SLEEP 360
ENTRYPOINT [ "uv", "run", "--frozen", "--no-sync", "python", "-m", "updater" ]
