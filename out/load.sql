-- Generated load script for PostgreSQL
-- Run from project root, then: psql -d <db> -f out/load.sql
BEGIN;

COPY training_jobs (job_id, job_type, status, created_at, started_at, finished_at, params, error_message) FROM './out/training_jobs.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY model_registry (model_version, model_type, created_at, trained_job_id, metrics, artifact_uri, is_active) FROM './out/model_registry.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY user_features (user_id, updated_at, category_counts, brand_counts, avg_check, last_k_items, last_active_ts) FROM './out/user_features.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY item_features (item_id, updated_at, category_id, price, discount, seller_id, rating, is_available) FROM './out/item_features.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY rec_requests (request_id, user_id, context, category_id, item_id, ts, model_version, latency_ms) FROM './out/rec_requests.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY rec_results (request_id, position, item_id, score, reason_code) FROM './out/rec_results.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY rec_feedback (feedback_id, request_id, user_id, item_id, action, ts) FROM './out/rec_feedback.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY moderation_requests (mod_request_id, item_id, seller_id, title, description, category_id, attributes, ts, model_version) FROM './out/moderation_requests.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY moderation_decisions (mod_request_id, decision, confidence, reason_code, decided_at) FROM './out/moderation_decisions.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
COPY ai_events (event_id, event_type, user_id, item_id, order_id, session_id, ts, payload) FROM './out/ai_events.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

COMMIT;
