-- PostgreSQL Database Initialization Script
-- Phase 3.3: 데이터베이스 초기 설정
--
-- 이 스크립트는 Docker Compose 또는 초기 설치 시 실행됩니다.

-- 필수 확장 설치
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- pg_stat_statements 설정 (쿼리 성능 모니터링)
-- 주의: postgresql.conf에 shared_preload_libraries = 'pg_stat_statements' 추가 필요
-- ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';

-- 연결 수 모니터링 뷰
CREATE OR REPLACE VIEW v_connection_stats AS
SELECT
    datname as database,
    usename as username,
    state,
    count(*) as connections,
    max(now() - backend_start) as max_connection_age
FROM pg_stat_activity
WHERE datname IS NOT NULL
GROUP BY datname, usename, state
ORDER BY connections DESC;

-- 슬로우 쿼리 모니터링 함수
CREATE OR REPLACE FUNCTION get_slow_queries(threshold_ms INTEGER DEFAULT 100)
RETURNS TABLE (
    query TEXT,
    calls BIGINT,
    total_time_ms DOUBLE PRECISION,
    mean_time_ms DOUBLE PRECISION,
    rows_returned BIGINT
) AS $$
BEGIN
    -- pg_stat_statements 확장이 설치된 경우에만 동작
    IF EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
    ) THEN
        RETURN QUERY
        SELECT
            pss.query::TEXT,
            pss.calls,
            pss.total_exec_time as total_time_ms,
            pss.mean_exec_time as mean_time_ms,
            pss.rows as rows_returned
        FROM pg_stat_statements pss
        WHERE pss.mean_exec_time > threshold_ms
        ORDER BY pss.mean_exec_time DESC
        LIMIT 20;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 테이블 통계 모니터링 뷰
CREATE OR REPLACE VIEW v_table_stats AS
SELECT
    schemaname,
    relname as table_name,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    CASE WHEN n_live_tup > 0
        THEN round((n_dead_tup::numeric / n_live_tup * 100)::numeric, 2)
        ELSE 0
    END as dead_row_percent,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- 인덱스 사용 통계 뷰
CREATE OR REPLACE VIEW v_index_usage AS
SELECT
    schemaname,
    relname as table_name,
    indexrelname as index_name,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- 사용되지 않는 인덱스 찾기
CREATE OR REPLACE VIEW v_unused_indexes AS
SELECT
    schemaname,
    relname as table_name,
    indexrelname as index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND indexrelname NOT LIKE '%_pkey'  -- Primary key 제외
ORDER BY pg_relation_size(indexrelid) DESC;

-- 테이블/인덱스 크기 모니터링 뷰
CREATE OR REPLACE VIEW v_table_sizes AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) as table_size,
    pg_size_pretty(pg_indexes_size(schemaname || '.' || tablename)) as indexes_size,
    (SELECT count(*) FROM pg_indexes WHERE tablename = t.tablename) as index_count
FROM pg_tables t
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;

-- Lock 모니터링 뷰
CREATE OR REPLACE VIEW v_locks AS
SELECT
    l.locktype,
    l.relation::regclass as table_name,
    l.mode,
    l.granted,
    a.usename,
    a.query,
    a.state,
    now() - a.query_start as query_duration
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE l.relation IS NOT NULL
    AND a.query NOT LIKE '%pg_locks%'
ORDER BY query_duration DESC;

-- 데이터베이스 권한 부여 안내
-- 프로덕션에서는 적절한 사용자와 권한을 설정하세요
-- GRANT CONNECT ON DATABASE poker TO poker_user;
-- GRANT USAGE ON SCHEMA public TO poker_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO poker_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO poker_user;

COMMENT ON VIEW v_connection_stats IS '연결 통계 모니터링';
COMMENT ON VIEW v_table_stats IS '테이블 통계 및 vacuum 상태';
COMMENT ON VIEW v_index_usage IS '인덱스 사용 통계';
COMMENT ON VIEW v_unused_indexes IS '사용되지 않는 인덱스 목록';
COMMENT ON VIEW v_table_sizes IS '테이블 및 인덱스 크기';
COMMENT ON VIEW v_locks IS '현재 Lock 상태';
