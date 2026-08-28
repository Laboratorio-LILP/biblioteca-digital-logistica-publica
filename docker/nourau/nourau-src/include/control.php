<?php

// NOU-RAU - Copyright (C) 2002 Instituto Vale do Futuro
// This program is free software; see COPYING for details.

/*-------------- includes --------------*/

require_once BASE . 'include/page.php';
require_once BASE . 'include/util.php';
require_once BASE . 'include/util_t.php';


/*-------------- access control functions --------------*/

function is_administrator ()
{
  
  return isset($_SESSION['suid'], $_SESSION['slevel']) && (int) $_SESSION['slevel'] === ADM_LEVEL;
}

function is_maintainer ()
{
 
  return isset($_SESSION['suid'], $_SESSION['slevel']) && (int) $_SESSION['slevel'] === MNT_LEVEL;
}


function is_responsable()
{
  return isset($_SESSION['suid'], $_SESSION['slevel']) && (int) $_SESSION['slevel'] === RES_LEVEL;
}


function is_collab ()
{
  
  return isset($_SESSION['suid'], $_SESSION['slevel']) && (int) $_SESSION['slevel'] === USR_LEVEL;
}


function is_user ()
{
 
  //return session_is_registered('session') && $_SESSION['slevel'] >= SEC_LEVEL;
  
  return isset($_SESSION['suid'], $_SESSION['slevel']) && (int) $_SESSION['slevel'] >= USR_LEVEL;
}

function check_administrator_rights ()
{
  global $cfg_site;
  global $REQUEST_URI, $session;

  if (!isset($_SESSION['suid']))
    redirect("{$cfg_site}user/login.php?url=" . rawurlencode($_SERVER['REQUEST_URI']));

  if (isset($_SESSION['slevel']) && (int) $_SESSION['slevel'] === ADM_LEVEL)
    return;

  error_teses(_('Access denied'));
}

function check_maintainer_rights ($tid = '')
{
  global $cfg_site;
  global $REQUEST_URI, $session;

  //echo "Level = " $_SESSION['slevel'] ." - ";

  if (!isset($_SESSION['suid']))
    redirect("{$cfg_site}user/login.php?url=" . rawurlencode($REQUEST_URI));

  $slevel = isset($_SESSION['slevel']) ? (int) $_SESSION['slevel'] : 0;

  if ($slevel === ADM_LEVEL)
    return;
  if ($slevel === MNT_LEVEL) {
    if (empty($tid) || check_topic_users($tid, $_SESSION['suid']) == TRUE)
      return;
    else
      message($cfg_site,"Documento não encontrado", "failure");
  }
  if ($slevel === RES_LEVEL) {
    if (empty($tid) || check_topic_users($tid, $_SESSION['suid']) == TRUE)
      return;
    else
      message($cfg_site,"Documento não encontrado", "failure");
  }
   

  if ($slevel === USR_LEVEL)
    message($cfg_site,"Documento não encontrado", "failure");
  redirect("{$cfg_site}user/login.php?url=" . rawurlencode($REQUEST_URI));
}

function check_administrator_maintainer_rights ()
{
  global $cfg_site;
  global $REQUEST_URI, $session;

  if (!isset($_SESSION['suid']))
    redirect("{$cfg_site}user/login.php?url=" . rawurlencode($REQUEST_URI));

  $slevel = isset($_SESSION['slevel']) ? (int) $_SESSION['slevel'] : 0;

  if ($slevel >= MNT_LEVEL)
    return;
  if ($slevel === USR_LEVEL)
    error_teses(_('Access denied').$_SESSION['slevel']);
redirect("{$cfg_site}user/login.php?url=" . rawurlencode($REQUEST_URI));
}

function check_user_rights ()
{
  global $cfg_site;
  global $REQUEST_URI, $session;

  if (isset($_SESSION['suid'], $_SESSION['slevel']) && (int) $_SESSION['slevel'] >= USR_LEVEL)
    return;
  redirect("{$cfg_site}user/login.php?url=" . rawurlencode($REQUEST_URI));
}


?>
