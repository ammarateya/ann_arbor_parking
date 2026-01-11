-- Citations table stores parsed data from the portal
create table if not exists public.citations (
  citation_number       bigint primary key,
  location              text,
  plate_state           text,
  plate_number          text,
  vin                   text,
  issue_date            timestamp with time zone,
  due_date              timestamp with time zone,
  status                text,
  amount_due            numeric(12,2),
  more_info_url         text,
  raw_html              text,
  issuing_agency        text,
  comments              text,
  violations            jsonb,
  image_urls            jsonb,
  -- Officer info extracted from receipt images via OCR
  officer_badge         text,
  officer_name          text,
  officer_beat          text,
  officer_info_extracted_at timestamp with time zone,
  -- Location/geocoding
  latitude              double precision,
  longitude             double precision,
  geocoded_at           timestamp with time zone,
  -- Timestamps
  created_at            timestamp with time zone default now(),
  scraped_at            timestamp with time zone default now()
);


-- Scraper state tracks last successful citation processed
create table if not exists public.scraper_state (
  id                              int primary key default 1,
  last_successful_citation        bigint,
  last_citation_seen_at           timestamp with time zone,
  last_no_citation_email_sent_at  timestamp with time zone,
  updated_at                      timestamp with time zone default now()
);

-- Ensure single row state table
insert into public.scraper_state (id, last_successful_citation, last_citation_seen_at, last_no_citation_email_sent_at)
values (1, null, null, null)
on conflict (id) do nothing;

-- Logs of search attempts
create table if not exists public.scrape_logs (
  id             bigserial primary key,
  search_term    text not null,
  found_results  boolean not null,
  error_message  text,
  created_at     timestamp with time zone default now()
);

-- Backblaze B2 stored images
create table if not exists public.citation_images_b2 (
  id                bigserial primary key,
  citation_number   bigint references public.citations(citation_number) on delete cascade,
  original_url      text not null,
  b2_filename       text not null,
  b2_file_id        text not null,
  b2_download_url   text,
  file_size_bytes   bigint,
  content_type      text,
  content_hash      text,
  upload_timestamp  timestamp with time zone default now(),
  created_at        timestamp with time zone default now()
);

-- Legacy images table (keeping for backward compatibility)
create table if not exists public.citation_images (
  id                bigserial primary key,
  citation_number   bigint references public.citations(citation_number) on delete cascade,
  source_url        text not null,
  local_path        text,
  remote_url        text,
  created_at        timestamp with time zone default now()
);

-- Helpful indexes
create index if not exists idx_citations_issue_date on public.citations (issue_date);
create index if not exists idx_citations_plate on public.citations (plate_state, plate_number);
create index if not exists idx_citations_location on public.citations (latitude, longitude);
create index if not exists idx_citations_officer_badge on public.citations (officer_badge);
create index if not exists idx_citations_officer_name on public.citations (officer_name);
create index if not exists idx_citation_images_citation on public.citation_images (citation_number);
create index if not exists idx_citation_images_b2_citation on public.citation_images_b2 (citation_number);
create index if not exists idx_citation_images_b2_hash on public.citation_images_b2 (content_hash);
create index if not exists idx_citation_images_b2_filename on public.citation_images_b2 (b2_filename);