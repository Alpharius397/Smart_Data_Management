-- Postgres User-defined Functions --

CREATE OR REPLACE FUNCTION jsonjoin (x jsonb, y jsonb, OUT y jsonb) 
    AS 'SELECT x::jsonb || y::jsonb' 
LANGUAGE SQL;

CREATE OR REPLACE AGGREGATE jsonsum (jsonb)(
    sfunc = jsonjoin,
    stype = jsonb,
    initcond = '{}'
);
