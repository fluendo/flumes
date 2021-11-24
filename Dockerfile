FROM ubuntu:20.04

ARG FLUMES_VERSION
ENV FLUMES_DIR=/data
ENV FLUMES_URI=sqlite:///flumes.db

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

RUN apt-get update
RUN apt-get install -y python3.9 python3-pip libcairo2-dev libpython3.9-dev libgirepository1.0-dev libgstreamer-plugins-base1.0-dev
RUN python3.9 -m pip install flumes==$FLUMES_VERSION
CMD flumes-discovery -d $FLUMES_DIR -i $FLUMES_URI
