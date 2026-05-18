package com.watermarking.infrastructure.persistence;

import com.watermarking.domain.model.File;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

public interface FileRepository extends JpaRepository<File, Integer> {

    Page<File> findByUploader_IdOrderByCreatedAtDesc(Integer uploaderId, Pageable pageable);

    Page<File> findByUploader_IdAndFileTypeOrderByCreatedAtDesc(Integer uploaderId, String fileType, Pageable pageable);

    Page<File> findByUploader_IdAndFilenameContainingIgnoreCaseOrderByCreatedAtDesc(
            Integer uploaderId, String filename, Pageable pageable);

    Optional<File> findByIdAndUploader_Id(Integer id, Integer uploaderId);

    List<File> findByUploader_IdAndCreatedAtBefore(Integer uploaderId, Instant cutoff);

    @Query("select coalesce(sum(f.fileSize), 0) from File f")
    long sumAllFileSizes();

    @Query("select coalesce(sum(f.fileSize), 0) from File f where f.uploader.id = :uid")
    long sumFileSizesForUploader(@Param("uid") int uid);

    @Query("select count(f) from File f where f.hasWatermark = true")
    long countWithWatermark();

    @Query("select count(f) from File f where f.uploader.id = :uid and f.hasWatermark = true")
    long countWithWatermarkForUploader(@Param("uid") int uid);

    @Query("select count(f) from File f where f.uploader.id = :uid")
    long countForUploader(@Param("uid") int uid);

    @Query("select f.fileType, count(f) from File f group by f.fileType")
    List<Object[]> countGroupedByFileType();

    @Query("select f.fileType, count(f) from File f where f.uploader.id = :uid group by f.fileType")
    List<Object[]> countGroupedByFileTypeForUploader(@Param("uid") int uid);

    @Query(
            value =
                    "select date(created_at) as d, count(*) as c from files where created_at >= :start "
                            + "group by date(created_at) order by d",
            nativeQuery = true)
    List<Object[]> countUploadsByDayGlobal(@Param("start") Instant start);

    @Query(
            value =
                    "select date(created_at) as d, count(*) as c from files where uploader_id = :uid and created_at >= :start "
                            + "group by date(created_at) order by d",
            nativeQuery = true)
    List<Object[]> countUploadsByDayForUploader(@Param("uid") int uid, @Param("start") Instant start);
}
