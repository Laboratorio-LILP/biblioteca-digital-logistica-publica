<?php

// NOU-RAU - Copyright (C) 2002 Instituto Vale do Futuro
// This program is free software; see COPYING for details.

require_once '../include/start.php';
require_once BASE . 'include/page_u.php';
require_once BASE . 'include/format.php';
require_once BASE . 'include/util.php';
echo "<!DOCTYPE html>";
echo "<head>";
echo "<meta charset='UTF-8' />";
echo "<title>Formulário de Login e Registro com HTML5 e CSS3</title>";
echo "<meta name='viewport' content='width=device-width, initial-scale=1.0'> ";
echo "<link rel='stylesheet' type='text/css' href='../layout/estilo_login.css' />";
echo "</head>";


$captcha = isset($_POST['g-recaptcha-response']) ? $_POST['g-recaptcha-response'] : null;
/* 
if(!is_null($captcha)){
	$res = json_decode(file_get_contents("https://www.google.com/recaptcha/api/siteverify?secret=PASTE-YOUR-SECRET_KEY-HERE&response=".$captcha."&remoteip=".$_SERVER['REMOTE_ADDR']));
	if($res->success === true){
		//CAPTCHA validado!!!
		echo 'Tudo certo =)';
	}
	else{
		echo 'Erro ao validar o captcha!!!';
	}
}
else{
	echo 'Captcha não preenchido!';
}*/
// filter input

if($_SERVER["REQUEST_METHOD"] == "POST") {

   $sent = trim($_POST['sent']);
   $username = trim($_POST['username']);
   $password = trim($_POST['password']);
    
   $nusername = strtolower(trim($_POST['username']));

   $recaptcha = $_POST['g-recaptcha-response'];
 
}

// validate input
if (empty($sent))
  form();
if (empty($username))
  form(_('Please specify an identification'));
if (empty($password))
  form(_('Please specify a password')); 

if($recaptcha == true) {
    $res = reCaptcha($recaptcha,$recaptcha_secret);
    if(!$res['success'])
       form('Captcha não preenchido!'); 
} 


// check username and password
$q = db_query("SELECT id,password,level FROM users WHERE username='$username'");
if (!db_rows($q))
  form('Identificação ou senha inválida');
$a = db_fetch_array($q);
if (rot13($password) != $a['password'])
  form('Identificação ou senha inválida');

// initialize session

session_name($cfg_session_name."_".uniqid());
$_SESSION['suid'] = $a['id'];
$_SESSION['susername'] = $nusername;
$_SESSION['slevel'] = $a['level'];

// update last access
db_command("UPDATE users SET accessed='now' WHERE id='{$_SESSION['suid']}'");
add_log('c', 'ul');

// finish
if ($_SESSION['slevel'] == '0')
    redirect("{$cfg_site}document/list.php?tid=675");
if (empty($url))
  redirect($cfg_site);
else
  redirect($url);


/*-------------- functions --------------*/

function form ($msg = "")
{
  global  $username, $url, $recaptcha, $recaptcha_key, $recaptcha_secret;

  //page_begin();
  echo "<div class ='container' id='mainContent1'>"; 
  echo "<div class='content'>";
  echo "<div id='login'>"; 
 	  
	  
	  html_form_begin($_SERVER['PHP_SELF']);
	  echo html_h1('Acesso BDU');
	  
	   format_warning($msg);
      //echo "<p>Acesso restrito para os funcionários do Sistema de Biblioteca da Unicamp.</p>";
	  html_form_text('Identificação', 'username', 15, $username, 15, true, 'Nome do usuário');  
	  html_form_password('Senha', 'password', 10, '', 10, true, '1234');

    if ($recaptcha == true)
      echo "<p><div class='g-recaptcha' data-sitekey='".$recaptcha_key."'></div></p>";
		   
	  html_form_hidden('url', $url);


	  html_form_submit('Acessar', 'sent');
	  html_form_end();
	  
  echo "</div><!--#login-->\n";
  echo "</div><!--#content-->\n";
  

  /*echo html_p(format_action(_('Remind forgotten identification or password'),
                            "{$cfg_site}user/remind.php"));*/
   
   echo "</div><!--#mainContent1-->\n";
 
 /*if (empty($url))
    page_end($cfg_site);
  else
    page_end($url);*/
  exit();
}

function reCaptcha($recaptcha,$secret){
  $ip = $_SERVER['REMOTE_ADDR'];
  $postvars = array("secret"=>$secret, "response"=>$recaptcha, "remoteip"=>$ip);
  $url = "https://www.google.com/recaptcha/api/siteverify";
  $ch = curl_init();
  curl_setopt($ch, CURLOPT_URL, $url);
  curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
  curl_setopt($ch, CURLOPT_TIMEOUT, 10);
  curl_setopt($ch, CURLOPT_POSTFIELDS, $postvars);
  $data = curl_exec($ch);
  curl_close($ch);

  return json_decode($data, true);
}


?>
