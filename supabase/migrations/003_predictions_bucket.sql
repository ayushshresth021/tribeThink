-- Predictions bucket — stores serialised numpy arrays from TribeV2 inference
insert into storage.buckets (id, name, public)
values ('predictions', 'predictions', false)
on conflict (id) do nothing;

create policy "Service role manages predictions"
  on storage.objects for all
  to service_role
  using (bucket_id = 'predictions')
  with check (bucket_id = 'predictions');
