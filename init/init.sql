-- Postgres User-defined Functions --

CREATE FUNCTION jsonjoin (x jsonb, y jsonb, OUT y jsonb) 
    AS 'SELECT x::jsonb || y::jsonb' 
LANGUAGE SQL;

CREATE AGGREGATE jsonsum (jsonb)(
    sfunc = jsonjoin,
    stype = jsonb,
    initcond = '{}'
);