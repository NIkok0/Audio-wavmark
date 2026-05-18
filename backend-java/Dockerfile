# 在 backend-java 目录构建：docker build -t watermark-api:local .
# 运行需传入 WM_* 环境变量或挂载 application-prod.yml（见 docs/DEPLOY-SERVER.md）

FROM maven:3.9-eclipse-temurin-17-alpine AS build
WORKDIR /src
COPY pom.xml .
COPY domain ./domain
COPY infrastructure ./infrastructure
COPY application ./application
COPY web ./web
RUN mvn -B -q -pl web -am package -DskipTests \
    && cp web/target/*.jar /tmp/app.jar

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
RUN addgroup -S wm && adduser -S wm -G wm
COPY --from=build /tmp/app.jar /app/app.jar
USER wm
EXPOSE 8080
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app/app.jar"]
