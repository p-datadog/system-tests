FROM datadog/system-tests:uwsgi-poc.base-v1

WORKDIR /app

# this is necessary for the mysqlclient install
RUN apt update && apt install -y pkg-config default-libmysqlclient-dev pkg-config

RUN pip install boto3 kombu mock asyncpg aiomysql mysql-connector-python pymysql mysqlclient

COPY utils/build/docker/python/install_ddtrace.sh utils/build/docker/python/get_appsec_rules_version.py binaries* /binaries/
RUN /binaries/install_ddtrace.sh

COPY utils/build/docker/python/flask /app
COPY utils/build/docker/python/iast.py /app/iast.py
ENV FLASK_APP=app.py

ENV DD_TRACE_HEADER_TAGS='user-agent:http.request.headers.user-agent'
ENV DD_REMOTECONFIG_POLL_SECONDS=1
ENV _DD_APPSEC_DEDUPLICATION_ENABLED=false

# docker startup
# note, only thread mode is supported
# https://ddtrace.readthedocs.io/en/stable/advanced_usage.html#uwsgi
RUN echo '#!/bin/bash \n\
ddtrace-run uwsgi --http :7777 -w app:app --enable-threads\n' > app.sh
RUN chmod +x app.sh
CMD ./app.sh

# docker build -f utils/build/docker/python.flask-poc.Dockerfile -t test .
# docker run -ti -p 7777:7777 test

