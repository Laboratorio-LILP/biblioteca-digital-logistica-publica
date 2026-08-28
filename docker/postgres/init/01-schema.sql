--
-- COMMON DATABASE - schema 1.0.0
-- Nou-Rau: Sistema de Armazenamento e Indexação de Documentos Digitais
--

CREATE FUNCTION _ (VARCHAR) RETURNS VARCHAR AS 'SELECT $1' LANGUAGE 'sql';

CREATE SEQUENCE notice_seq MINVALUE 0;
CREATE SEQUENCE topic_seq  MINVALUE 0;
CREATE SEQUENCE users_seq  MINVALUE 0;

CREATE TABLE log (
  scope           CHAR,
  op              CHAR(2),
  user_id         INT,
  logged          timestamp without time zone DEFAULT ('now'::text)::timestamp(6) with time zone,
  level           CHAR,
  info            VARCHAR(400)
);

CREATE TABLE notice (
  id              INT DEFAULT NEXTVAL('notice_seq'),
  subject         VARCHAR(100),
  notice          VARCHAR(1000),
  user_id         INT,
  posted          timestamp without time zone DEFAULT ('now'::text)::timestamp(6) with time zone,
  PRIMARY KEY (id)
);

CREATE TABLE topic (
  id              INT DEFAULT NEXTVAL('topic_seq'),
  name            VARCHAR(300),
  description     VARCHAR(300),
  parent_id       INT DEFAULT '0',
  maintainer_id   INT,
  options         VARCHAR(2000) DEFAULT '',
  created         timestamp without time zone DEFAULT ('now'::text)::timestamp(6) with time zone,
  tipo_acesso     INT DEFAULT '0',
  archieve        CHAR DEFAULT 's',
  url             VARCHAR(150),
  remote          CHAR DEFAULT 'n',
  PRIMARY KEY (id)
);

CREATE TABLE topic_path (
  topic_id        INT,
  parent_ids      VARCHAR(200),
  parent_names    VARCHAR(2000),
  changed         CHAR DEFAULT 'n',
  PRIMARY KEY (topic_id)
);

--
-- ⚠️ CREDENCIAIS. A coluna password comporta um hash moderno (bcrypt/argon2
-- cabem em 255), mas o Nou-Rau AINDA grava rot13() do texto claro — formato
-- reversível, não um hash. Trocar o esquema exige mudar junto o seed de
-- 03-reset.sql e as comparações literais em
-- docker/nourau/nourau-src/user/{login,loginsemrecatcha,change}.php, e remover
-- o envio da senha por e-mail de .../user/remind.php — nada disso foi feito
-- aqui. O acesso da role read-only do portal a esta tabela é retirado em
-- 10-portal-readonly-revoke-users.sql.
--
CREATE TABLE users (
  id             INT DEFAULT NEXTVAL('users_seq'),
  username       VARCHAR(10) UNIQUE,
  password       VARCHAR(255),
  name           VARCHAR(100),
  email          VARCHAR(50),
  info           VARCHAR(500) DEFAULT '',
  options        VARCHAR(2000) DEFAULT '',
  level          CHAR DEFAULT '1',
  accessed       timestamp without time zone DEFAULT ('now'::text)::timestamp(6) with time zone,
  PRIMARY KEY (id)
);

CREATE TABLE user_registration (
  email           VARCHAR(50),
  code            INT,
  motive          VARCHAR(250) DEFAULT '',
  status          CHAR DEFAULT 'w',
  requested       timestamp without time zone DEFAULT ('now'::text)::timestamp(6) with time zone,
  PRIMARY KEY (email)
);

CREATE TABLE version (
  schema          VARCHAR(10)
);
