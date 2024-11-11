FROM ghcr.io/datadog/images-rb/engines/ruby:3.1

RUN mkdir -p /app
WORKDIR /app

COPY utils/build/docker/ruby/sinatra21/ .

COPY utils/build/docker/ruby/install_ddtrace.sh binaries* /binaries/
RUN /binaries/install_ddtrace.sh

ENV DD_TRACE_HEADER_TAGS=user-agent
ENV DD_APM_RECEIVER_SOCKET=/var/run/datadog/apm.socket

COPY utils/build/docker/set-uds-transport.sh set-uds-transport.sh
RUN echo "#!/bin/bash\n./set-uds-transport.sh\nbundle exec puma -b tcp://0.0.0.0 -p 7777 -w 1" > app.sh
RUN chmod +x app.sh
CMD [ "./app.sh" ]
