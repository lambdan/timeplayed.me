-- needed if upgrading from < 3.4.0
ALTER TABLE public.activity ADD COLUMN emulated boolean DEFAULT false;
