FROM selenium/standalone-chrome

USER root
RUN apt-get update && apt-get install -y redis-tools

WORKDIR /reg

ADD register.sh /reg/

RUN chmod +x /reg/register.sh

USER seluser

CMD /reg/register.sh

