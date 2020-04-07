CREATE TABLE songs
(
  song_id serial not null,
  song_name varchar(250) NOT NULL,
  artist_id int NOT NULL,
  album varchar(300) DEFAULT NULL,
  file_name varchar(100) NOT NULL,
  file_path varchar(300) NOT NULL,
  genre varchar(50) NOT NULL,
  track_number smallint DEFAULT NULL,
  year char(4) DEFAULT NULL,
  comment text DEFAULT NULL,
  duration smallint DEFAULT NULL,
  bit_rate varchar(20) DEFAULT NULL,
  created_date timestamp NOT NULL default now(),
  last_updated_date timestamp NOT NULL DEFAULT now(),
  last_updated_by varchar(20) NOT NULL
);

