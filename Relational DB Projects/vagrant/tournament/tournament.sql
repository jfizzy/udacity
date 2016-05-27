-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

CREATE TABLE Players(  id SERIAL UNIQUE,
                      name TEXT,
                      wins integer DEFAULT 0,
                      matches integer DEFAULT 0);

CREATE TABLE Matches(   id SERIAL UNIQUE,
                      winner integer NOT NULL,
                      loser integer NOT NULL);
