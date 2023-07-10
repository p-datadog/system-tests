FROM ghcr.io/datadog/dd-trace-rb/ruby:2.6.7-dd

RUN curl -O https://rubygems.org/downloads/libv8-node-16.10.0.0-$(arch)-linux.gem && gem install libv8-node-16.10.0.0-$(arch)-linux.gem && rm libv8-node-16.10.0.0-$(arch)-linux.gem && gem install mini_racer:'0.6.2'

RUN mkdir -p /app
WORKDIR /app

COPY utils/build/docker/ruby/rails51/ .
COPY utils/build/docker/ruby/install_ddtrace.sh binaries* /binaries/
RUN /binaries/install_ddtrace.sh

ENV DD_TRACE_HEADER_TAGS=user-agent

RUN echo "#!/bin/bash\nbundle exec rails db:create db:migrate db:seed\nbundle exec puma -b tcp://0.0.0.0 -p 7777 -w 1" > app.sh
RUN chmod +x app.sh
CMD [ "./app.sh" ]
