-- needed if upgrading from < 4.8.0
ALTER TABLE public.platform ADD COLUMN color_primary varchar(6);
ALTER TABLE public.platform ADD COLUMN color_secondary varchar(6);
ALTER TABLE public.platform ADD COLUMN icon varchar(50);
