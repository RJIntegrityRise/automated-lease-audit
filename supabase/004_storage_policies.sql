create policy "Users can upload lease documents"
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'lease-documents'
  and auth.uid() is not null
  and (storage.foldername(name))[1] = auth.uid()::text
);

create policy "Users can view their lease documents"
on storage.objects
for select
to authenticated
using (
  bucket_id = 'lease-documents'
  and auth.uid() is not null
  and (storage.foldername(name))[1] = auth.uid()::text
);

create policy "Users can update their lease documents"
on storage.objects
for update
to authenticated
using (
  bucket_id = 'lease-documents'
  and auth.uid() is not null
  and (storage.foldername(name))[1] = auth.uid()::text
)
with check (
  bucket_id = 'lease-documents'
  and auth.uid() is not null
  and (storage.foldername(name))[1] = auth.uid()::text
);

create policy "Users can delete their lease documents"
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'lease-documents'
  and auth.uid() is not null
  and (storage.foldername(name))[1] = auth.uid()::text
);