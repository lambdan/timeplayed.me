-- Full schema of storage_v2 as of evolution 15 (pg_dump --schema-only of prod, 2026-10-29).
-- Fresh installs: apply this, then any evolutions numbered higher than 15.
-- Existing installs: ignore this file and keep applying evolutions as usual.

--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2 (Debian 17.2-1.pgdg120+1)
-- Dumped by pg_dump version 17.2 (Debian 17.2-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: activity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.activity (
    id integer NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    game_id integer NOT NULL,
    platform_id integer NOT NULL,
    seconds integer NOT NULL,
    user_id bigint,
    hidden boolean DEFAULT false NOT NULL,
    created timestamp with time zone DEFAULT now(),
    updated timestamp with time zone DEFAULT now()
);


--
-- Name: activity_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.activity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: activity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.activity_id_seq OWNED BY public.activity.id;


--
-- Name: discordhistory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.discordhistory (
    id integer NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    event text NOT NULL,
    "user" character varying(255),
    message text NOT NULL
);


--
-- Name: discordhistory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.discordhistory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: discordhistory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.discordhistory_id_seq OWNED BY public.discordhistory.id;


--
-- Name: game; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    sgdb_id integer,
    image_url character varying(255),
    aliases text[] NOT NULL,
    release_year integer,
    hidden boolean DEFAULT false NOT NULL,
    created timestamp with time zone DEFAULT now(),
    updated timestamp with time zone DEFAULT now(),
    parent_id integer,
    search character varying(255) DEFAULT ''::character varying NOT NULL,
    sgdb_grid_id integer,
    igdb_id integer,
    steam_id integer
);


--
-- Name: game_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.game_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: game_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.game_id_seq OWNED BY public.game.id;


--
-- Name: history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.history (
    id integer NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    game_id integer,
    user_id integer,
    platform_id integer,
    activity_id integer,
    message text
);


--
-- Name: history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.history_id_seq OWNED BY public.history.id;


--
-- Name: liveactivity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.liveactivity (
    id integer NOT NULL,
    game_id integer NOT NULL,
    platform_id integer NOT NULL,
    started timestamp without time zone NOT NULL,
    user_id bigint
);


--
-- Name: liveactivity_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.liveactivity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: liveactivity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.liveactivity_id_seq OWNED BY public.liveactivity.id;


--
-- Name: platform; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.platform (
    id integer NOT NULL,
    abbreviation character varying(255) NOT NULL,
    name character varying(255),
    color_primary character varying(6),
    color_secondary character varying(6),
    icon character varying(50),
    created timestamp with time zone DEFAULT now(),
    updated timestamp with time zone DEFAULT now(),
    search character varying(255) DEFAULT ''::character varying NOT NULL
);


--
-- Name: platform_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.platform_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: platform_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.platform_id_seq OWNED BY public.platform.id;


--
-- Name: token; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.token (
    id integer NOT NULL,
    created timestamp without time zone NOT NULL,
    user_id integer NOT NULL,
    sha256 text NOT NULL
);


--
-- Name: token_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.token_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: token_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.token_id_seq OWNED BY public.token.id;


--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."user" (
    id bigint DEFAULT nextval('public.user_id_seq'::regclass) NOT NULL,
    discord_id character varying(255),
    name character varying(255) NOT NULL,
    default_platform_id integer NOT NULL,
    pc_platform character varying(255) DEFAULT 'win'::character varying,
    permissions text[] DEFAULT '{commands,manual_activity,oblivionis_sync}'::text[],
    created timestamp with time zone DEFAULT now(),
    updated timestamp with time zone DEFAULT now(),
    search character varying(255) DEFAULT ''::character varying NOT NULL,
    display_name character varying(255) DEFAULT NULL::character varying
);


--
-- Name: activity id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity ALTER COLUMN id SET DEFAULT nextval('public.activity_id_seq'::regclass);


--
-- Name: discordhistory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discordhistory ALTER COLUMN id SET DEFAULT nextval('public.discordhistory_id_seq'::regclass);


--
-- Name: game id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game ALTER COLUMN id SET DEFAULT nextval('public.game_id_seq'::regclass);


--
-- Name: history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.history ALTER COLUMN id SET DEFAULT nextval('public.history_id_seq'::regclass);


--
-- Name: liveactivity id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liveactivity ALTER COLUMN id SET DEFAULT nextval('public.liveactivity_id_seq'::regclass);


--
-- Name: platform id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform ALTER COLUMN id SET DEFAULT nextval('public.platform_id_seq'::regclass);


--
-- Name: token id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token ALTER COLUMN id SET DEFAULT nextval('public.token_id_seq'::regclass);


--
-- Name: activity activity_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity
    ADD CONSTRAINT activity_pkey PRIMARY KEY (id);


--
-- Name: discordhistory discordhistory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discordhistory
    ADD CONSTRAINT discordhistory_pkey PRIMARY KEY (id);


--
-- Name: game game_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game
    ADD CONSTRAINT game_pkey PRIMARY KEY (id);


--
-- Name: game game_steam_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game
    ADD CONSTRAINT game_steam_id_key UNIQUE (steam_id);


--
-- Name: history history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.history
    ADD CONSTRAINT history_pkey PRIMARY KEY (id);


--
-- Name: liveactivity liveactivity_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liveactivity
    ADD CONSTRAINT liveactivity_pkey PRIMARY KEY (id);


--
-- Name: platform platform_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform
    ADD CONSTRAINT platform_pkey PRIMARY KEY (id);


--
-- Name: token token_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token
    ADD CONSTRAINT token_pkey PRIMARY KEY (id);


--
-- Name: token token_sha256_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token
    ADD CONSTRAINT token_sha256_key UNIQUE (sha256);


--
-- Name: user users_new_discord_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT users_new_discord_id_key UNIQUE (discord_id);


--
-- Name: user users_new_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT users_new_pkey PRIMARY KEY (id);


--
-- Name: activity_game_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX activity_game_id ON public.activity USING btree (game_id);


--
-- Name: activity_platform_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX activity_platform_id ON public.activity USING btree (platform_id);


--
-- Name: activity_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX activity_user_id ON public.activity USING btree (user_id);


--
-- Name: game_aliases; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX game_aliases ON public.game USING gin (aliases);


--
-- Name: game_parent_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX game_parent_id ON public.game USING btree (parent_id);


--
-- Name: game_search_trgm_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX game_search_trgm_idx ON public.game USING gin (search public.gin_trgm_ops);


--
-- Name: liveactivity_game_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX liveactivity_game_id ON public.liveactivity USING btree (game_id);


--
-- Name: liveactivity_platform_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX liveactivity_platform_id ON public.liveactivity USING btree (platform_id);


--
-- Name: liveactivity_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX liveactivity_user_id ON public.liveactivity USING btree (user_id);


--
-- Name: platform_abbreviation; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX platform_abbreviation ON public.platform USING btree (abbreviation);


--
-- Name: platform_search_trgm_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX platform_search_trgm_idx ON public.platform USING gin (search public.gin_trgm_ops);


--
-- Name: user_default_platform_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_default_platform_id ON public."user" USING btree (default_platform_id);


--
-- Name: user_discord_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX user_discord_id ON public."user" USING btree (discord_id);


--
-- Name: user_permissions; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_permissions ON public."user" USING gin (permissions);


--
-- Name: user_search_trgm_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_search_trgm_idx ON public."user" USING gin (search public.gin_trgm_ops);


--
-- Name: activity activity_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity
    ADD CONSTRAINT activity_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(id);


--
-- Name: activity activity_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity
    ADD CONSTRAINT activity_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES public.platform(id);


--
-- Name: activity activity_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity
    ADD CONSTRAINT activity_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: game game_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game
    ADD CONSTRAINT game_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.game(id) ON DELETE SET NULL;


--
-- Name: history history_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.history
    ADD CONSTRAINT history_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.activity(id) ON DELETE CASCADE;


--
-- Name: history history_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.history
    ADD CONSTRAINT history_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(id) ON DELETE CASCADE;


--
-- Name: history history_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.history
    ADD CONSTRAINT history_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES public.platform(id) ON DELETE CASCADE;


--
-- Name: history history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.history
    ADD CONSTRAINT history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: liveactivity liveactivity_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liveactivity
    ADD CONSTRAINT liveactivity_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(id);


--
-- Name: liveactivity liveactivity_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liveactivity
    ADD CONSTRAINT liveactivity_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES public.platform(id);


--
-- Name: liveactivity liveactivity_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liveactivity
    ADD CONSTRAINT liveactivity_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: token token_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token
    ADD CONSTRAINT token_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: user users_new_default_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT users_new_default_platform_id_fkey FOREIGN KEY (default_platform_id) REFERENCES public.platform(id);


--
-- PostgreSQL database dump complete
--

