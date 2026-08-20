alter table public.profiles
add column if not exists approval_status text
not null
default 'pending';

alter table public.profiles
add column if not exists approved_by uuid
references public.profiles(id);

alter table public.profiles
add column if not exists approved_at timestamptz;

alter table public.profiles
add constraint profiles_approval_status_check
check (
  approval_status in (
    'pending',
    'approved',
    'rejected'
  )
);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (
    id,
    full_name,
    role,
    active,
    approval_status
  )
  values (
    new.id,
    coalesce(
      new.raw_user_meta_data ->> 'full_name',
      new.email
    ),
    'reviewer',
    true,
    'pending'
  );

  return new;
end;
$$;