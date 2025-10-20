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
  created_at            timestamp with time zone default now(),
  scraped_at            timestamp with time zone default now()
);

-- Scraper state tracks last successful citation processed
create table if not exists public.scraper_state (
  id                         int primary key default 1,
  last_successful_citation   bigint,
  updated_at                 timestamp with time zone default now()
);

-- Ensure single row state table
insert into public.scraper_state (id, last_successful_citation)
values (1, null)
on conflict (id) do nothing;

-- Logs of search attempts
create table if not exists public.scrape_logs (
  id             bigserial primary key,
  search_term    text not null,
  found_results  boolean not null,
  error_message  text,
  created_at     timestamp with time zone default now()
);

-- Helpful indexes
create index if not exists idx_citations_issue_date on public.citations (issue_date);
create index if not exists idx_citations_plate on public.citations (plate_state, plate_number);

-- Optional images table to track local/remote storage
create table if not exists public.citation_images (
  id                bigserial primary key,
  citation_number   bigint references public.citations(citation_number) on delete cascade,
  source_url        text not null,
  local_path        text,
  remote_url        text,
  created_at        timestamp with time zone default now()
);
create index if not exists idx_citation_images_citation on public.citation_images (citation_number);


