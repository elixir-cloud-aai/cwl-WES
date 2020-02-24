FROM alpine:20191114
MAINTAINER Juhani Kataja <juhani.kataja@csc.fi>

RUN apk update && apk add certbot
RUN apk add curl
RUN mkdir -p /etc/letsencrypt /var/log/letsencrypt

COPY secret-patch-template.json /
COPY route-patch-template.json /
COPY entrypoint.sh /

# Following two lines are for debugging purposes
RUN chmod 774 /entrypoint.sh
RUN chmod 664 /secret-patch-template.json
RUN chmod 775 /var/log/letsencrypt /etc/letsencrypt

CMD ["/entrypoint.sh"]

