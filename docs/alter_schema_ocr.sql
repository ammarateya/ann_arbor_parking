-- Officers table
create table if not exists public.officers (
  id bigserial primary key,
  officer_number text not null,
  officer_name text not null,
  constraint officers_unique unique (officer_number, officer_name)
);

-- Add OCR-enriched columns to citations if not present
do $$ begin
  if not exists (select 1 from information_schema.columns where table_name='citations' and column_name='vehicle_make') then
    alter table public.citations add column vehicle_make text;
  end if;
  if not exists (select 1 from information_schema.columns where table_name='citations' and column_name='vehicle_model') then
    alter table public.citations add column vehicle_model text;
  end if;
  if not exists (select 1 from information_schema.columns where table_name='citations' and column_name='vehicle_color') then
    alter table public.citations add column vehicle_color text;
  end if;
  if not exists (select 1 from information_schema.columns where table_name='citations' and column_name='plate_exp_month') then
    alter table public.citations add column plate_exp_month int;
  end if;
  if not exists (select 1 from information_schema.columns where table_name='citations' and column_name='plate_exp_year') then
    alter table public.citations add column plate_exp_year int;
  end if;
  if not exists (select 1 from information_schema.columns where table_name='citations' and column_name='district_number') then
    alter table public.citations add column district_number int;
  end if;
  if not exists (select 1 from information_schema.columns where table_name='citations' and column_name='meter_number') then
    alter table public.citations add column meter_number text;
  end if;
  if not exists (select 1 from information_schema.columns where table_name='citations' and column_name='ocr_location') then
    alter table public.citations add column ocr_location text;
  end if;
end $$;

-- Optional cleanup: drop officer columns if they exist
do $$ begin
  if exists (select 1 from information_schema.columns where table_name='citations' and column_name='officer_number') then
    alter table public.citations drop column officer_number;
  end if;
  if exists (select 1 from information_schema.columns where table_name='citations' and column_name='officer_name') then
    alter table public.citations drop column officer_name;
  end if;
end $$;

-- Add geocoding columns for map display
do $$ begin
  if not exists (select 1 from information_schema.columns where table_name='citations' and column_name='latitude') then
    alter table public.citations add column latitude double precision;
  end if;
  if not exists (select 1 from information_schema.columns where table_name='citations' and column_name='longitude') then
    alter table public.citations add column longitude double precision;
  end if;
  if not exists (select 1 from information_schema.columns where table_name='citations' and column_name='geocoded_at') then
    alter table public.citations add column geocoded_at timestamp with time zone;
  end if;
end $$;

-- Subscriptions for notifications (email and/or webhook) by plate
create table if not exists public.subscriptions (
  id                bigserial primary key,
  plate_state       text not null,
  plate_number      text not null,
  email             text,
  webhook_url       text,
  is_active         boolean not null default true,
  created_at        timestamp with time zone default now(),
  constraint subscriptions_contact_check check (email is not null or webhook_url is not null),
  unique (plate_state, plate_number, coalesce(email,''), coalesce(webhook_url,''))
);

create index if not exists idx_subscriptions_plate on public.subscriptions (plate_state, plate_number) where is_active;

-- Extend subscriptions to support location-based alerts
do $$ begin
  if not exists (select 1 from information_schema.columns where table_name='subscriptions' and column_name='sub_type') then
    alter table public.subscriptions add column sub_type text default 'plate';
  end if;
  if not exists (select 1 from information_schema.columns where table_name='subscriptions' and column_name='center_lat') then
    alter table public.subscriptions add column center_lat double precision;
  end if;
  if not exists (select 1 from information_schema.columns where table_name='subscriptions' and column_name='center_lon') then
    alter table public.subscriptions add column center_lon double precision;
  end if;
  if not exists (select 1 from information_schema.columns where table_name='subscriptions' and column_name='radius_m') then
    alter table public.subscriptions add column radius_m double precision;
  end if;
end $$;

create index if not exists idx_subscriptions_location on public.subscriptions (is_active, sub_type);

