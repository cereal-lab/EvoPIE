FROM ubuntu:20.04

RUN apt update -y && \
    apt upgrade -y
RUN apt install -y python3 python3-pip
RUN pip3 install pipenv
RUN apt install -y sqlite3 git

WORKDIR /app
RUN git clone https://github.com/cereal-lab/EvoPIE.git

WORKDIR /app/EvoPIE
RUN echo "START" ; pipenv sync



ENTRYPOINT [ "pipenv", "run", "flask", "run" ]
