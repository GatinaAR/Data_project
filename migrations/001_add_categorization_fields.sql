-- Run once against news.db before starting categorize_news.py.
BEGIN IMMEDIATE;

ALTER TABLE articles
    ADD COLUMN category_status TEXT NOT NULL DEFAULT 'pending';

ALTER TABLE articles
    ADD COLUMN category_attempts INTEGER NOT NULL DEFAULT 0;

ALTER TABLE articles
    ADD COLUMN category_error TEXT;

ALTER TABLE articles
    ADD COLUMN categorized_at TEXT;

-- Preserve articles that already have a real category.
UPDATE articles
SET category_status = 'success'
WHERE category IS NOT NULL
  AND TRIM(category) <> ''
  AND category <> 'Без категории';

CREATE INDEX IF NOT EXISTS idx_articles_category_status_date
    ON articles (category_status, published_date DESC, id DESC);

COMMIT;
