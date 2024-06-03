FROM ubuntu:20.04

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y && \
    apt-get upgrade -y
RUN apt-get install -y python3 python3-pip
RUN pip3 install pipenv
RUN apt-get install -y sqlite3 git
RUN apt-get install -y nmap
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata
RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

ENV TZ="America/New_York"

WORKDIR /app
RUN echo "forcing rebuild  "
RUN git clone https://github.com/cereal-lab/EvoPIE.git .
RUN git checkout master
RUN git pull

RUN pipenv sync
#RUN pipenv run flask DB-reboot

ENV EVOPIE_UPDATER_SLEEP 360
ENTRYPOINT [ "pipenv", "run", "python", "-m", "updater" ]
