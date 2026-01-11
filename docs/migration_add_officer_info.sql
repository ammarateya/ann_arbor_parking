-- Migration: Add officer info columns to citations table
-- Run this in your Supabase SQL Editor or via psql

-- Add officer columns
ALTER TABLE public.citations 
ADD COLUMN IF NOT EXISTS officer_badge text,
ADD COLUMN IF NOT EXISTS officer_name text,
ADD COLUMN IF NOT EXISTS officer_beat text,
ADD COLUMN IF NOT EXISTS officer_info_extracted_at timestamp with time zone;

-- Add index for officer queries
CREATE INDEX IF NOT EXISTS idx_citations_officer_badge ON public.citations (officer_badge);
CREATE INDEX IF NOT EXISTS idx_citations_officer_name ON public.citations (officer_name);

-- Comment on columns
COMMENT ON COLUMN public.citations.officer_badge IS 'Badge number of the officer who issued the citation';
COMMENT ON COLUMN public.citations.officer_name IS 'Name of the officer who issued the citation';
COMMENT ON COLUMN public.citations.officer_beat IS 'Beat/patrol area of the officer';
COMMENT ON COLUMN public.citations.officer_info_extracted_at IS 'Timestamp when officer info was extracted via OCR';
