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

