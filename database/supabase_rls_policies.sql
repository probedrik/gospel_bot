-- NOTE: current schema uses user_id BIGINT (telegram id).
-- Service-role backend will bypass all policies.

-- Helper: returns TRUE if a relation exists in current database
-- Usage: to_regclass('public.table_name') is not null

-- users
do $$
begin
  if to_regclass('public.users') is not null then
    alter table public.users enable row level security;
    drop policy if exists "users_select_own" on public.users;
    drop policy if exists "users_upsert_own" on public.users;
    create policy "users_select_own" on public.users
      for select using (
        current_setting('request.jwt.claim.sub', true) is not null and
        current_setting('request.jwt.claim.sub', true) = user_id::text
      );
    create policy "users_upsert_own" on public.users
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- ai_limits
do $$
begin
  if to_regclass('public.ai_limits') is not null then
    alter table public.ai_limits enable row level security;
    drop policy if exists "ai_limits_crud_own" on public.ai_limits;
    create policy "ai_limits_crud_own" on public.ai_limits
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- bookmarks
do $$
begin
  if to_regclass('public.bookmarks') is not null then
    alter table public.bookmarks enable row level security;
    drop policy if exists "bookmarks_crud_own" on public.bookmarks;
    create policy "bookmarks_crud_own" on public.bookmarks
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- ai_settings (no public access; server-only)
do $$
begin
  if to_regclass('public.ai_settings') is not null then
    alter table public.ai_settings enable row level security;
    -- no user policies; service role bypasses RLS
  end if;
end $$;

-- ai_usage
do $$
begin
  if to_regclass('public.ai_usage') is not null then
    alter table public.ai_usage enable row level security;
    drop policy if exists "ai_usage_crud_own" on public.ai_usage;
    create policy "ai_usage_crud_own" on public.ai_usage
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- bible_topics (optional: uncomment to allow public read)
do $$
begin
  if to_regclass('public.bible_topics') is not null then
    alter table public.bible_topics enable row level security;
    -- drop policy if exists "bible_topics_public_read" on public.bible_topics;
    -- create policy "bible_topics_public_read" on public.bible_topics for select using (true);
  end if;
end $$;

-- reading_progress
do $$
begin
  if to_regclass('public.reading_progress') is not null then
    alter table public.reading_progress enable row level security;
    drop policy if exists "reading_progress_crud_own" on public.reading_progress;
    create policy "reading_progress_crud_own" on public.reading_progress
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- reading_parts_progress
do $$
begin
  if to_regclass('public.reading_parts_progress') is not null then
    alter table public.reading_parts_progress enable row level security;
    drop policy if exists "reading_parts_progress_crud_own" on public.reading_parts_progress;
    create policy "reading_parts_progress_crud_own" on public.reading_parts_progress
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- reading_plans (optional: uncomment to allow public read)
do $$
begin
  if to_regclass('public.reading_plans') is not null then
    alter table public.reading_plans enable row level security;
    -- drop policy if exists "reading_plans_public_read" on public.reading_plans;
    -- create policy "reading_plans_public_read" on public.reading_plans for select using (true);
  end if;
end $$;

-- reading_plan_days (optional: uncomment to allow public read)
do $$
begin
  if to_regclass('public.reading_plan_days') is not null then
    alter table public.reading_plan_days enable row level security;
    -- drop policy if exists "reading_plan_days_public_read" on public.reading_plan_days;
    -- create policy "reading_plan_days_public_read" on public.reading_plan_days for select using (true);
  end if;
end $$;

-- user_reading_plans
do $$
begin
  if to_regclass('public.user_reading_plans') is not null then
    alter table public.user_reading_plans enable row level security;
    drop policy if exists "user_reading_plans_crud_own" on public.user_reading_plans;
    create policy "user_reading_plans_crud_own" on public.user_reading_plans
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- premium_requests
do $$
begin
  if to_regclass('public.premium_requests') is not null then
    alter table public.premium_requests enable row level security;
    drop policy if exists "premium_requests_crud_own" on public.premium_requests;
    create policy "premium_requests_crud_own" on public.premium_requests
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- premium_purchases
do $$
begin
  if to_regclass('public.premium_purchases') is not null then
    alter table public.premium_purchases enable row level security;
    drop policy if exists "premium_purchases_crud_own" on public.premium_purchases;
    create policy "premium_purchases_crud_own" on public.premium_purchases
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- donations
do $$
begin
  if to_regclass('public.donations') is not null then
    alter table public.donations enable row level security;
    drop policy if exists "donations_crud_own" on public.donations;
    create policy "donations_crud_own" on public.donations
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- saved_commentaries (owned by user)
do $$
begin
  if to_regclass('public.saved_commentaries') is not null then
    alter table public.saved_commentaries enable row level security;
    drop policy if exists "saved_commentaries_crud_own" on public.saved_commentaries;
    create policy "saved_commentaries_crud_own" on public.saved_commentaries
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- star_transactions (owned by user)
do $$
begin
  if to_regclass('public.star_transactions') is not null then
    alter table public.star_transactions enable row level security;
    drop policy if exists "star_transactions_crud_own" on public.star_transactions;
    create policy "star_transactions_crud_own" on public.star_transactions
      for all using (current_setting('request.jwt.claim.sub', true) = user_id::text)
      with check (current_setting('request.jwt.claim.sub', true) = user_id::text);
  end if;
end $$;

-- books (public read)
do $$
begin
  if to_regclass('public.books') is not null then
    alter table public.books enable row level security;
    drop policy if exists "books_public_read" on public.books;
    create policy "books_public_read" on public.books for select using (true);
  end if;
end $$;

-- verses (public read)
do $$
begin
  if to_regclass('public.verses') is not null then
    alter table public.verses enable row level security;
    drop policy if exists "verses_public_read" on public.verses;
    create policy "verses_public_read" on public.verses for select using (true);
  end if;
end $$;

