CREATE TABLE artists
( 
  artist_id serial not null,
  full_name varchar(200) NOT NULL,
  first_name varchar(200),
  last_name varchar(200),
  created_date timestamp NOT NULL default now(),
  last_updated_date timestamp NOT NULL DEFAULT now(),
  last_updated_by varchar(20) NOT NULL
);
