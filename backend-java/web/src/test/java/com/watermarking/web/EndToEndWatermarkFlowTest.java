package com.watermarking.web;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.watermarking.infrastructure.config.WmJobsProperties;
import com.watermarking.infrastructure.storage.UploadObjectKeyBuilder;
import jakarta.servlet.http.Cookie;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3Configuration;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * MySQL + Redis + MinIO Testcontainers：注册 → 登录 → S3 登记文件（complete）→ 入队水印任务 → 模拟 Worker 更新 Redis 任务态。
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Testcontainers(disabledWithoutDocker = true)
class EndToEndWatermarkFlowTest {

    private static final byte[] TINY_PNG = Base64.getDecoder()
            .decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==");

    @Container
    private static final MySQLContainer<?> MYSQL =
            new MySQLContainer<>(DockerImageName.parse("mysql:8.0"))
                    .withDatabaseName("watermark")
                    .withUsername("dev")
                    .withPassword("devpass");

    @Container
    private static final GenericContainer<?> REDIS =
            new GenericContainer<>(DockerImageName.parse("redis:7-alpine")).withExposedPorts(6379);

    @Container
    private static final GenericContainer<?> MINIO =
            new GenericContainer<>(DockerImageName.parse("minio/minio:RELEASE.2024-05-10T01-41-38Z"))
                    .withCommand("server", "/data", "--console-address", ":9001")
                    .withEnv("MINIO_ROOT_USER", "minioadmin")
                    .withEnv("MINIO_ROOT_PASSWORD", "minioadmin")
                    .withExposedPorts(9000);

    private static Path instanceDir;

    @DynamicPropertySource
    static void registerContainers(DynamicPropertyRegistry registry) throws Exception {
        if (instanceDir == null) {
            instanceDir = Files.createTempDirectory("wm-e2e-instance");
            instanceDir.toFile().deleteOnExit();
        }
        registry.add("spring.datasource.url", MYSQL::getJdbcUrl);
        registry.add("spring.datasource.username", MYSQL::getUsername);
        registry.add("spring.datasource.password", MYSQL::getPassword);

        registry.add("spring.data.redis.host", REDIS::getHost);
        registry.add("spring.data.redis.port", () -> String.valueOf(REDIS.getMappedPort(6379)));

        String minioHost = MINIO.getHost();
        int minioPort = MINIO.getMappedPort(9000);
        String minioEndpoint = "http://" + minioHost + ":" + minioPort;
        registry.add("wm.storage.backend", () -> "minio");
        registry.add("wm.storage.minio.endpoint", () -> minioEndpoint);
        registry.add("wm.storage.minio.access-key", () -> "minioadmin");
        registry.add("wm.storage.minio.secret-key", () -> "minioadmin");
        registry.add("wm.storage.minio.bucket", () -> "watermark");
        registry.add("wm.storage.minio.region", () -> "us-east-1");
        registry.add("wm.storage.instance-path", () -> instanceDir.toAbsolutePath().toString().replace('\\', '/'));
    }

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private org.springframework.data.redis.core.StringRedisTemplate stringRedisTemplate;

    @Autowired
    private WmJobsProperties wmJobsProperties;

    @Test
    void registerLoginCompleteFileEnqueueJobAndMockWorkerCompletion() throws Exception {
        String suffix = UUID.randomUUID().toString().substring(0, 8);
        String username = "u" + suffix;
        String email = "e" + suffix + "@example.com";
        String password = "secret12";

        mockMvc.perform(
                        post("/api/v1/auth/register")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"username":"%s","email":"%s","password":"%s"}
                                        """
                                                .formatted(username, email, password)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").exists());

        MvcResult loginResult =
                mockMvc.perform(
                                post("/api/v1/auth/login")
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content(
                                                """
                                                {"usernameOrEmail":"%s","password":"%s"}
                                                """
                                                        .formatted(username, password)))
                        .andExpect(status().isOk())
                        .andReturn();

        Cookie session = loginResult.getResponse().getCookie("WMSESSIONID");
        assertThat(session).isNotNull();

        String loginBody = loginResult.getResponse().getContentAsString(StandardCharsets.UTF_8);
        int userId = objectMapper.readTree(loginBody).path("id").asInt();

        String objectKey = UploadObjectKeyBuilder.build(userId, "image", "probe.png");
        uploadPngToMinio(objectKey);

        S3Client probe = buildS3Client();
        var head = probe.headObject(h -> h.bucket("watermark").key(objectKey));
        String etag = head.eTag();
        long size = head.contentLength();
        probe.close();

        MvcResult completeResult =
                mockMvc.perform(
                                post("/api/v1/files/complete")
                                        .cookie(session)
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content(
                                                """
                                                {"objectKey":"%s","etag":"%s","size":%d,"filename":"probe.png","mediaType":"image"}
                                                """
                                                        .formatted(objectKey, etag, size)))
                        .andExpect(status().isOk())
                        .andExpect(jsonPath("$.id").exists())
                        .andReturn();

        int fileId = objectMapper.readTree(completeResult.getResponse().getContentAsString(StandardCharsets.UTF_8))
                .path("id")
                .asInt();

        MvcResult jobResult =
                mockMvc.perform(
                                post("/api/v1/jobs/watermark")
                                        .cookie(session)
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content(
                                                """
                                                {"fileId":%d,"watermarkText":"wm-e2e"}
                                                """
                                                        .formatted(fileId)))
                        .andExpect(status().isAccepted())
                        .andExpect(jsonPath("$.jobId").exists())
                        .andExpect(jsonPath("$.status").value("QUEUED"))
                        .andReturn();

        JsonNode jobJson =
                objectMapper.readTree(jobResult.getResponse().getContentAsString(StandardCharsets.UTF_8));
        String jobId = jobJson.path("jobId").asText();

        Long streamLen = stringRedisTemplate.opsForStream().size(wmJobsProperties.getStreamKey());
        assertThat(streamLen).isNotNull();
        assertThat(streamLen).isGreaterThanOrEqualTo(1);

        long now = System.currentTimeMillis();
        stringRedisTemplate.opsForHash().put(wmJobsProperties.jobHashKey(jobId), "status", "COMPLETED");
        stringRedisTemplate.opsForHash().put(wmJobsProperties.jobHashKey(jobId), "updatedAt", String.valueOf(now));

        mockMvc.perform(get("/api/v1/jobs/" + jobId).cookie(session))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("COMPLETED"));
    }

    private S3Client buildS3Client() {
        String endpoint = "http://" + MINIO.getHost() + ":" + MINIO.getMappedPort(9000);
        return S3Client.builder()
                .region(Region.US_EAST_1)
                .endpointOverride(URI.create(endpoint))
                .credentialsProvider(
                        StaticCredentialsProvider.create(AwsBasicCredentials.create("minioadmin", "minioadmin")))
                .serviceConfiguration(S3Configuration.builder().pathStyleAccessEnabled(true).build())
                .httpClient(UrlConnectionHttpClient.create())
                .build();
    }

    private void uploadPngToMinio(String objectKey) {
        try (S3Client client = buildS3Client()) {
            client.putObject(
                    PutObjectRequest.builder().bucket("watermark").key(objectKey).contentType("image/png").build(),
                    RequestBody.fromBytes(TINY_PNG));
        }
    }
}
