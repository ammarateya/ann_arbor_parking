# Fix "Auth Needed" Error on Localhost:5000

## Quick Fix

The map requires authentication to read citations from your Supabase database. Here's how to fix it:

### Option 1: Add Service Role Key (Recommended)

1. **Get your Supabase Service Role Key:**

   - Go to your Supabase dashboard: https://supabase.com/dashboard
   - Select your project
   - Go to Settings → API
   - Copy the "service_role" key (not the anon key!)

2. **Add it to your environment:**

   If you're using a `.env` file:

   ```bash
   # Add this line to your .env file
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
   ```

   If you're running directly:

   ```bash
   export SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
   ```

3. **Restart your server:**
   ```bash
   python main.py
   ```

### Option 2: Disable RLS (Less Secure)

If you're okay with making your data publicly readable:

1. Go to your Supabase dashboard
2. Go to Authentication → Policies
3. Find the `citations` table
4. Disable Row Level Security (RLS)

⚠️ **Note**: This makes your data publicly accessible without authentication!

### Option 3: Add RLS Policies (More Secure)

Create a policy that allows reading citations:

1. In Supabase SQL Editor, run:

```sql
CREATE POLICY "Allow public read access to citations"
ON public.citations
FOR SELECT
USING (true);
```

This allows anyone to read citations (but not modify them).

## Verify It's Working

1. Start your server: `python main.py`
2. Visit `http://localhost:5000`
3. Check browser console (F12) for any errors
4. You should see the map with citations loaded

## Troubleshooting

**Still seeing errors?**

- Check that your `.env` file is in the project root
- Make sure you're using the service_role key (not anon key)
- Verify your SUPABASE_URL is correct
- Check the server logs for specific error messages

**Empty map?**

- You need to geocode citations first: `python geocode_citations.py`
- Check that citations have coordinates in the database
- Look for "Citation missing coordinates" messages in browser console
