<?php

// NOU-RAU - Copyright (C) 2002 Instituto Vale do Futuro
// This program is free software; see COPYING for details.

/*-------------- database --------------*/

// name of PostgreSQL database

$cfg_base = 'nourau';
$cfg_host = 'localhost';
$cfg_port = '5432';

// name of PostgreSQL user (and password, if needed)
$cfg_user = 'php';
$cfg_pass = 'OVERWRITTEN_AT_BOOT_BY_ENVSUBST';  // regenerado pelo entrypoint via envsubst (POSTGRES_PASSWORD)

/*-------------- site --------------*/
// site host address
$cfg_host_site = "localhost";

// site base address
$cfg_site = $cfg_host_site."/manager/";

//link do site WP - Exemplo = https://www.bibliotecadigital.unicamp.br/bd/index.php/detalhes-material/?code=
$cfg_site_wp = "";

//site  image address
$cfg_dir_image ="$cfg_host_site/images/capas";

// site title
$cfg_site_title = 'Sistema Nou-Rau';


/*-------------- e-mail --------------*/

// webmaster contact e-mail
$cfg_webmaster = 'nourau@localhost.com';

// subject tag for outgoing e-mail
$cfg_subject_tag = 'NouRau';

// should redirect all outgoing e-mail to webmaster?
$cfg_redirect_emails = false;

// should obfuscate all e-mail addresses shown to prevent SPAM?
$cfg_obfuscate_emails = true;

/*-------------- layout --------------*/

// banner settings
$cfg_logo_url  = "$cfg_site/images/logo-nr.png";


/*-------------- miscellaneous --------------*/

// cookie name where session id is stored
$cfg_session_name = $cfg_base;

// uncomment this to go offline

define('HALT', false);

//RECAPTCHA 

//Habilitar o RECAPTCHA(see http://www.google.com/recaptcha)
$recaptcha = false;

//Chave de site para reCaptcha 
$recaptcha_key = "";

#Chave publica para reCaptcha 
$recaptcha_secret = "";

?>
