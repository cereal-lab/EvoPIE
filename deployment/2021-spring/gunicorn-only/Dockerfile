FROM ubuntu:20.04

RUN apt update -y && \
    apt upgrade -y
RUN apt install -y python3 python3-pip
RUN pip3 install pipenv
RUN apt install -y sqlite3 git

WORKDIR /app
RUN echo "forcing rebuild"
RUN git clone https://github.com/cereal-lab/EvoPIE.git

WORKDIR /app/EvoPIE
RUN pipenv sync
#RUN pipenv run flask DB-reboot

#ENTRYPOINT [ "pipenv", "run", "flask", "run", "--host", "0.0.0.0" ]
ENTRYPOINT [ "pipenv", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:APP" ]
# docker build -t evopie .
# docker run -d -p 5000:5000 -v /EvoPIE/DB_quizlib.sqlite:/app/EvoPIE/evopie/DB_quizlib.sqlite evopie
# for windows local testing
# docker run -d -p 5000:5000 -v /mnt/c/Users/aless/OneDrive/Desktop/dev/EvoPIE/evopie/DB_quizlib.sqlite:/app/EvoPIE/evopie/DB_quizlib.sqlite evopie