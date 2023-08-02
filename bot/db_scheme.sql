--
-- PostgreSQL database dump
--
-- Dumped from database version 13.8
-- Dumped by pg_dump version 15.3
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: adm
--
-- *not* creating schema, since initdb creates it
ALTER SCHEMA public OWNER TO adm;
SET default_tablespace = '';
SET default_table_access_method = heap;
--
-- Name: maas_bot; Type: TABLE; Schema: public; Owner: adm
--
CREATE TABLE public.maas_bot (
    id bigint NOT NULL,
    username text,
    account_status text DEFAULT 'on',
    grafana_status text DEFAULT 'off',
    promalert_status text DEFAULT 'off',
    support_status text DEFAULT 'off',
    creation_time timestamp without time zone DEFAULT now(),
    grafana_deploy_time timestamp without time zone
);
ALTER TABLE public.maas_bot OWNER TO adm;
ALTER TABLE ONLY public.maas_bot
    ADD CONSTRAINT maas_bot_pkey PRIMARY KEY (id);
--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: adm
--
GRANT ALL ON SCHEMA public TO adm;
--
-- PostgreSQL database dump complete
--
