FROM ubuntu:16.04

ENV DOCKYARD_SRC=./

ENV DOCKYARD_SRVHOME=/opt/

ENV DOCKYARD_SRVPROJ=/opt/zergling/

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y python python-pip libmysqlclient-dev python-dev

WORKDIR $DOCKYARD_SRVHOME

COPY $DOCKYARD_SRC $DOCKYARD_SRVPROJ

RUN pip install -r $DOCKYARD_SRVPROJ/requirements.txt

WORKDIR $DOCKYARD_SRVPROJ

RUN mkdir logs

COPY ./docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]