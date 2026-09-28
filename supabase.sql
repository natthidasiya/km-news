-- (ไม่บังคับ) นับยอดถูกใจรวมทุกคน: รันครั้งเดียวใน Supabase > SQL Editor
create table if not exists likes (uid text primary key, n int not null default 0);
alter table likes enable row level security;
drop policy if exists "read" on likes; create policy "read" on likes for select using (true);
create or replace function like_news(p_uid text, p_delta int) returns int language sql security definer as $$
  insert into likes(uid,n) values (p_uid,greatest(p_delta,0))
  on conflict (uid) do update set n=greatest(likes.n+p_delta,0) returning n; $$;
grant execute on function like_news to anon;
