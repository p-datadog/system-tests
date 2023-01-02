
FROM eclipse-temurin:8 as agent

# Install required bsdtar
RUN apt-get update && \
	apt-get install -y libarchive-tools
# Install tracer
COPY ./utils/build/docker/java/install_ddtrace.sh binaries* /binaries/
RUN /binaries/install_ddtrace.sh


FROM ghcr.io/graalvm/graalvm-ce:ol8-java11-22 as build

# Install maven
RUN curl https://archive.apache.org/dist/maven/maven-3/3.8.6/binaries/apache-maven-3.8.6-bin.tar.gz --output /opt/maven.tar.gz && \
	tar xzvf /opt/maven.tar.gz --directory /opt && \
	rm /opt/maven.tar.gz

WORKDIR /app

# Copy application sources
COPY ./utils/build/docker/java/spring-boot/pom.xml .
COPY ./utils/build/docker/java/spring-boot/src ./src
RUN mv ./src/main/resources/application-native.properties ./src/main/resources/application.properties

# Copy tracer
COPY --from=agent /dd-tracer/dd-java-agent.jar .

# Build native application
RUN --mount=type=cache,target=/root/.m2 /opt/apache-maven-3.8.6/bin/mvn package -P spring-native

FROM adoptopenjdk:11-jre-hotspot

WORKDIR /app
COPY --from=agent /binaries/SYSTEM_TESTS_LIBRARY_VERSION SYSTEM_TESTS_LIBRARY_VERSION
COPY --from=agent /binaries/SYSTEM_TESTS_LIBDDWAF_VERSION SYSTEM_TESTS_LIBDDWAF_VERSION
COPY --from=agent /binaries/SYSTEM_TESTS_APPSEC_EVENT_RULES_VERSION SYSTEM_TESTS_APPSEC_EVENT_RULES_VERSION
COPY --from=build /app/target/myproject .


ENV DD_TRACE_HEADER_TAGS='user-agent:http.request.headers.user-agent'

RUN echo "#!/bin/bash\n/app/myproject" > app.sh
RUN chmod +x app.sh
CMD [ "./app.sh" ]
