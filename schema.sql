--
-- PostgreSQL database dump
--

\restrict 6f0mkDcbAL2Dz2b6YYpfbYh6oGtlrcwk8kTMAy6cFUejEnb2pyBf94td1yU1X1v

-- Dumped from database version 18.0 (Homebrew)
-- Dumped by pg_dump version 18.0 (Homebrew)

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
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: consumption; Type: TABLE; Schema: public; Owner: meghanarendrasimha
--

CREATE TABLE public.consumption (
    transaction_id text NOT NULL,
    date date,
    inventory_id text,
    quantity_consumed integer,
    department text,
    staff_id text,
    shift text,
    consumption_reason text,
    remaining_stock integer,
    batch_lot text
);


ALTER TABLE public.consumption OWNER TO meghanarendrasimha;

--
-- Name: finance; Type: TABLE; Schema: public; Owner: meghanarendrasimha
--

CREATE TABLE public.finance (
    invoice_id text NOT NULL,
    vendor_id text,
    inventory_id text,
    purchase_date date,
    quantity integer,
    unit_cost numeric,
    total_cost numeric,
    payment_status text,
    account_code text,
    delivery_date date
);


ALTER TABLE public.finance OWNER TO meghanarendrasimha;

--
-- Name: inventory_master; Type: TABLE; Schema: public; Owner: meghanarendrasimha
--

CREATE TABLE public.inventory_master (
    date date,
    inventory_id text NOT NULL,
    opening_stock integer,
    quantity_consumed integer,
    quantity_restocked integer,
    closing_stock integer,
    vendor_id text,
    lead_time_days integer,
    department_count integer,
    min_stock integer,
    max_capacity integer,
    item_name text,
    form text,
    use text,
    item_type text,
    out_of_stock boolean,
    low_stock boolean,
    embedding public.vector(384)
);


ALTER TABLE public.inventory_master OWNER TO meghanarendrasimha;

--
-- Name: reorder_log; Type: TABLE; Schema: public; Owner: meghanarendrasimha
--

CREATE TABLE public.reorder_log (
    log_id integer NOT NULL,
    inventory_id text NOT NULL,
    item_name text NOT NULL,
    reorder_quantity integer NOT NULL,
    current_stock integer NOT NULL,
    status text NOT NULL,
    email_recipient text,
    email_subject text,
    email_body text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.reorder_log OWNER TO meghanarendrasimha;

--
-- Name: reorder_log_log_id_seq; Type: SEQUENCE; Schema: public; Owner: meghanarendrasimha
--

CREATE SEQUENCE public.reorder_log_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reorder_log_log_id_seq OWNER TO meghanarendrasimha;

--
-- Name: reorder_log_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: meghanarendrasimha
--

ALTER SEQUENCE public.reorder_log_log_id_seq OWNED BY public.reorder_log.log_id;


--
-- Name: vendor_master; Type: TABLE; Schema: public; Owner: meghanarendrasimha
--

CREATE TABLE public.vendor_master (
    vendor_id text NOT NULL,
    vendor_name text NOT NULL,
    contact_number text,
    default_lead_time_days integer,
    region text,
    vendor_rating numeric
);


ALTER TABLE public.vendor_master OWNER TO meghanarendrasimha;

--
-- Name: reorder_log log_id; Type: DEFAULT; Schema: public; Owner: meghanarendrasimha
--

ALTER TABLE ONLY public.reorder_log ALTER COLUMN log_id SET DEFAULT nextval('public.reorder_log_log_id_seq'::regclass);


--
-- Name: consumption consumption_pkey; Type: CONSTRAINT; Schema: public; Owner: meghanarendrasimha
--

ALTER TABLE ONLY public.consumption
    ADD CONSTRAINT consumption_pkey PRIMARY KEY (transaction_id);


--
-- Name: finance finance_pkey; Type: CONSTRAINT; Schema: public; Owner: meghanarendrasimha
--

ALTER TABLE ONLY public.finance
    ADD CONSTRAINT finance_pkey PRIMARY KEY (invoice_id);


--
-- Name: inventory_master inventory_master_pkey; Type: CONSTRAINT; Schema: public; Owner: meghanarendrasimha
--

ALTER TABLE ONLY public.inventory_master
    ADD CONSTRAINT inventory_master_pkey PRIMARY KEY (inventory_id);


--
-- Name: reorder_log reorder_log_pkey; Type: CONSTRAINT; Schema: public; Owner: meghanarendrasimha
--

ALTER TABLE ONLY public.reorder_log
    ADD CONSTRAINT reorder_log_pkey PRIMARY KEY (log_id);


--
-- Name: vendor_master vendor_master_pkey; Type: CONSTRAINT; Schema: public; Owner: meghanarendrasimha
--

ALTER TABLE ONLY public.vendor_master
    ADD CONSTRAINT vendor_master_pkey PRIMARY KEY (vendor_id);


--
-- Name: consumption consumption_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: meghanarendrasimha
--

ALTER TABLE ONLY public.consumption
    ADD CONSTRAINT consumption_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory_master(inventory_id);


--
-- Name: finance finance_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: meghanarendrasimha
--

ALTER TABLE ONLY public.finance
    ADD CONSTRAINT finance_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory_master(inventory_id);


--
-- Name: finance finance_vendor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: meghanarendrasimha
--

ALTER TABLE ONLY public.finance
    ADD CONSTRAINT finance_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendor_master(vendor_id);


--
-- PostgreSQL database dump complete
--

\unrestrict 6f0mkDcbAL2Dz2b6YYpfbYh6oGtlrcwk8kTMAy6cFUejEnb2pyBf94td1yU1X1v

