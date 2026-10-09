FROM ubuntu:20.04

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y && \
    apt-get upgrade -y
RUN apt-get install -y python3 python3-pip
RUN apt-get install -y sqlite3 git
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

#ENTRYPOINT [ "uv", "run", "--frozen", "--no-sync", "flask", "run", "--host", "0.0.0.0" ]
#ENTRYPOINT [ "uv", "run", "--frozen", "--no-sync", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:APP" ]
#ENTRYPOINT [ "uv", "run", "--frozen", "--no-sync", "gunicorn", "-w", "4", "-b", "0.0.0.0:5010", "app:APP" ]
ENTRYPOINT [ "./evopie/entrypoint.sh" ]

# docker build -t evopie .
# docker run -d -p 5000:5000 -v ./data:/app/data evopie
