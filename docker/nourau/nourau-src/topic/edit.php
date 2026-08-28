<?php

// NOU-RAU - Copyright (C) 2002 Instituto Vale do Futuro
// This program is free software; see COPYING for details.

require_once '../include/start.php';
require_once BASE . 'include/control.php';
require_once BASE . 'include/format.php';
require_once BASE . 'include/page_d.php';
require_once BASE . 'include/util_t.php';
require_once BASE . 'include/defs.php';


if($_SERVER["REQUEST_METHOD"] == "GET") {
	
    $tid = isset($_GET['tid'])?$_GET['tid']:0;
	$pid = $_GET['pid'];
}
else {

$tid = $_POST['tid'];
$pid = $_POST['pid'];
$sent = $_POST['sent'];
$name = trim($_POST['name']);
$description = trim($_POST['description']);
$url = trim($_POST['url']);
$tipoAcesso = (isset($_POST['tipoAcesso'])?$_POST['tipoAcesso']:0);
//$maintainer = trim($_POST['maintainer']);
$category = isset($_POST['category'])?$_POST['category']:NULL;
$tipoInformacao = isset($_POST['tipoInformacao'])?$_POST['tipoInformacao']:NULL;
$remote = isset($_POST['remoteURL'])?'s':'n';
$archieve =  isset($_POST['archieve'])?'s':'n';

}



// validate input
if (!valid_opt_int($pid) || !valid_opt_int($tid))
  message("$cfg_site}document/?code=" . rawurlencode($a['code']),"Parâmetro Inválido !", "failure");

$back = "{$cfg_site}document/list.php?tid=$pid";
//check_administrator_maintainer_rights();

// Controle de acesso -- nega por padrão. Precisa vir antes de qualquer leitura
// ou escrita: no caminho POST (com "sent") form()/page_begin() nunca é chamado,
// então a verificação de sessão de page_begin_aux() não é alcançada ao salvar.
// A sessão é lida diretamente aqui, sem depender de check_*_rights().
$suid   = (isset($_SESSION['suid'])   && valid_int($_SESSION['suid']))   ? (int) $_SESSION['suid']   : 0;
$slevel = (isset($_SESSION['slevel']) && valid_int($_SESSION['slevel'])) ? (int) $_SESSION['slevel'] : 0;

if ($suid <= 0 || $slevel < MNT_LEVEL)
  redirect("{$cfg_site}user/login.php?url=" . rawurlencode($_SERVER['REQUEST_URI']));

if ($slevel != ADM_LEVEL) {
  if (!empty($tid)) {
    // edição: só quem mantém esta coleção (topic_users) pode alterá-la
    if (!topic_maintained_by($tid, $suid))
      message($back,"Acesso Negado!", "failure");
  }
  else {
    // criação: coleção raiz é exclusiva do administrador; os demais só criam
    // sub-coleção sob uma coleção que já mantêm
    if (empty($pid) || !topic_maintained_by($pid, $suid))
      message($back,"Acesso Negado!", "failure");
  }
}


  // handle edit mode
  if (empty($sent)) { 
    // first time; load from base
		if (!empty($tid)) {
   		 load();
    	 form();
		}
  }
  else if ($sent == 'Cancelar') {
    // abort editing
    redirect("{$cfg_site}document/list.php?tid=$pid");
  }


// filter input


// validate input
if (empty($sent))
  form();


if (empty($name))
  form(_('Please specify the name'));
if (empty($description))
  form(_('Please specify the description'));


if (empty($tid)) {
  // insert new topic
  if (empty($pid))
    $pid = 0;

  db_command_params('INSERT INTO topic (name,  description,  url, tipo_acesso, parent_id, remote, archieve) VALUES ($1,$2,$3,$4,$5,$6,$7)', array($name, $description, $url, $tipoAcesso, $pid, $remote, $archieve));
  $tid = db_simple_query("SELECT CURRVAL('topic_seq')");
  add_log('c', 'tc', "tid=$tid");

  // insert categories
  
 if (!empty($category)) {
  if (count($category) > 0 ) 
    foreach ($category as $cid) 
	  db_command_params('INSERT INTO nr_topic_category (topic_id,category_id) VALUES ($1,$2)', array($tid, $cid));
 }
 
 
 if (!empty($tipoInformacao)) {
  if (count($tipoInformacao) > 0 ) 
    foreach ($tipoInformacao as $type) 
	  db_command_params('INSERT INTO topic_type (topic_id, type_id) VALUES ($1,$2)', array($tid, $type));
 }
 
  // promote new maintainer
  
  // db_command("UPDATE users SET level='" . MNT_LEVEL . "' WHERE id='$mid' AND level='" . USR_LEVEL . "'");

  // promote rights for users

 if ($pid==0){
		 $sql =  "SELECT id FROM users WHERE level ='".ADM_LEVEL."' OR options = 'M'";
		 $user = db_query($sql);
		 while ($a = db_fetch_array($user)) {
			db_command("INSERT INTO topic_users (users_id,topic_id) VALUES ('{$a['id']}','$tid')");
		 }

  }
else {
		 $sql =  "SELECT id FROM users WHERE level ='".ADM_LEVEL."' OR options = 'M'";
		  $user = db_query($sql);
		  while ($a = db_fetch_array($user)) {
			db_command("INSERT INTO topic_users (users_id,topic_id) VALUES ('{$a['id']}','$tid')");
		  }
  }

  // finish
 /* message(
          "{$cfg_site}document/list.php" . (($pid) ? "?tid=$pid" : ''));*/
   message($back,"Coleção criada.", "success");
}
else {
	  // get old maintainer
	   $old = get_topic($tid, 'maintainer_id');

	  // update topic info
	  db_command_params('UPDATE topic SET name=$1, description=$2, url=$3, tipo_acesso=$4, remote=$5, archieve=$6 WHERE id=$7', array($name, $description, $url, $tipoAcesso, $remote, $archieve, $tid));
	  add_log('c', 'tu', "tid=$tid");

	  // update categories
	  db_command_params('DELETE FROM nr_topic_category WHERE topic_id=$1', array($tid));
	   
	 if (!empty($category)) {
	  if (count($category) > 0 ) 
		foreach ($category as $cid) {
		   db_command_params('INSERT INTO nr_topic_category (topic_id,category_id) VALUES ($1,$2)', array($tid, $cid));
		}  
	 }
	 
	  db_command_params('DELETE FROM topic_type WHERE topic_id=$1', array($tid));
	 
	   if (!empty($tipoInformacao)) {
		  if (count($tipoInformacao) > 0 ) 
			foreach ($tipoInformacao as $type) 
			  db_command_params('INSERT INTO topic_type (topic_id, type_id) VALUES ($1,$2)', array($tid, $type));
	 }

/*  // change maintainers if needed
  if ($old != $mid) {
    // demote old maintainer
    db_command("UPDATE users SET level='" . USR_LEVEL . "' WHERE id='$old' AND level='" . MNT_LEVEL . "' AND id NOT IN (SELECT maintainer_id FROM topic)");

    // promote new maintainer
    db_command("UPDATE users SET level='" . MNT_LEVEL . "' WHERE id='$mid' AND level='" . USR_LEVEL . "'");
  }*/

  // finish
  // message(_('Topic updated'), "{$cfg_site}document/list.php?tid=$pid");*/
   message($back,"Coleção atualizada.", "success");
}


/*-------------- functions --------------*/

// Executa um comando com valores ligados (bind), para os dados vindos da
// requisição. include/db.php só aceita SQL já montado, então usa-se
// pg_query_params() com a mesma conexão global e o mesmo tratamento de erro.
function db_command_params ($sql, $params)
{
  global $db_conn;

  if (!($q = pg_query_params($db_conn, $sql, $params)))
    fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");
  return @pg_affected_rows($q);
}

// Verdadeiro se o usuário está vinculado (topic_users) à coleção informada.
// O vínculo é resolvido pelo id do próprio registro de topic, não por um
// identificador fornecido pela requisição.
function topic_maintained_by ($topic_id, $users_id)
{
  global $db_conn;

  $q = pg_query_params($db_conn, 'SELECT topic.id FROM topic INNER JOIN topic_users ON topic_users.topic_id = topic.id WHERE topic.id = $1 AND topic_users.users_id = $2', array($topic_id, $users_id));
  return ($q !== FALSE && pg_num_rows($q) > 0);
}

function form ($msg = "")
{
  global $cfg_site, $session;
  global  $tid, $pid, $name, $description, $remote, $url, $tipoAcesso ,$maintainer, $category, $archieve, $tipoInformacao;

 page_begin();

if (empty($tid))
    echo html_h("Criar um nova Coleção");
  else
    echo html_h("Editar a Coleção " . $name);
  format_warning($msg);

  


  html_form_begin($_SERVER['PHP_SELF'], true, 'multipart/form-data');

  html_form_hidden('pid', $pid);
  html_form_hidden('tid', $tid);

  html_form_text("Nome da Coleção", 'name', 80, $name, 100, true, 'Digite o nome do Coleção');
  
  html_form_text("Decrição", 'description', 80, $description, 150, true, 'Digite uma breve descrição sobre o Coleção');
 
  echo "<p>";
  echo "<input type=\"checkbox\" id=\"remoteURL\" name=\"remoteURL\" value=\"on\" ". ($remote=="s"?"checked='checked'":"")." onclick=\"mostraURL('".$remote."','".$url."');\" > O Conteúdo desta coleção estará disponível em outro site.";
  echo "</p><br>";
  
 echo "<div id=\"remoten\">";
 if ($remote =="s") { 
     html_form_text("Endereço Remoto", 'url', 80, $url, 150, false, '', 'URL do conteúdo hospedado remotamente');
 }	 
 else {
	html_form_hidden('url', $url); 
 }
 
echo "</div>";
  $default = (!empty($tipoAcesso)?$tipoAcesso:0);

  //$optuser = array (0=>"Geral", 1=>"Somente Unicamp" , 2=>"Acesso Restrito(A coleção fica com restrições de acesso, somente pessoas autorizadas poderão acessá-lo)");
  
  //html_form_radio('Tipo de Acesso', 'tipoAcesso', $optuser, $default); 


 
  if (empty($tipoInformacao)) {
	  $tipoInformacao =array();  
	 $q = db_query("SELECT type_id FROM topic_type WHERE topic_id=$pid");
	 if (db_rows($q) > 0){
		while ($a = db_fetch_array($q))
			array_push($tipoInformacao, $a['type_id']);
	 }	
	 
  }
    
	   $qti = db_query("SELECT id, name FROM type_information order by name");   

      echo html_b("Tipo de informação:") . "<br>\n";
	  
	  echo "<ul class=\"checkbox\">";
      while ($a = db_fetch_array($qti)) {
		   		   
		  if (in_array($a['id'],  $tipoInformacao))
				$checked = 'Checked';
			else 
			 $checked = '';
		 
             echo "<li><input type=\"checkbox\"  name=\"tipoInformacao[]\" value=\"{$a['id']}\" {$checked}> {$a['name']}</li>\n";
      }
	  echo "</ul>";
		 	

  echo "<br>";
 
  echo "<p>";
  echo "<input type=\"checkbox\" id=\"archieve\" name=\"archieve\" value=\"on\" ". ($archieve=="s"?"checked='checked'":"")." onclick=\"mostraTipoDoc(this.value);\" > Arquivar documento nesta coleção.";
  echo "</p>";
  
  echo "<div id=\"tipoDoc\">";
   
   if ($archieve == 's') {

		 // show categories for this topic
		 if (empty($category))
			$category = array();
			$qcat = db_query("SELECT id,name,description FROM nr_category ORDER BY name");
		 
		  echo html_b("Tipo de Documentos:") . "<br>\n";
		  
		  echo "<select name=\"category[]\" multiple size=\"4\">\n";
		  while ($a = db_fetch_array($qcat)) {
			if (in_array($a['id'], $category))
			  echo '<option selected ';
			else
			  echo '<option ';
			echo "value=\"{$a['id']}\">" . _($a['name']) . ' - ' . _($a['description']) . "</option>\n";
		  }
		  echo "</select><p>\n";
		  
   }
 echo "</div><br />";
 
 
 
 echo "<div class=\"botao\">";
		html_form_submit('Salvar', 'sent');
		echo "</div>";
		echo "<div class=\"botao\">";
		html_form_submit('Cancelar', 'sent', FALSE);
	echo "</div>";


  html_form_end();


  if (empty($tid))
    page_end("{$cfg_site}document/list.php" . (($pid) ? "?tid=$pid" : ''));
  else
    page_end("{$cfg_site}document/list.php?tid=$tid");
  exit();
}

function load ()
{
  global $tid, $name, $description,  $maintainer, $category, $tipoAcesso, $pid, $url, $remote, $archieve, $tipoInformacao;

  $a = get_topic($tid);

  $name = $a['name'];
  $description = $a['description'];
  //$maintainer = get_user($a['maintainer_id'], 'username');
  //$maintainer = get_user($a['maintainer_id'], 'username');
  $remote = $a['remote'];
  $archieve = $a['archieve'];
  $url = $a['url'];
  $tipoAcesso = $a['tipo_acesso'];
  $pid =  $a['parent_id'];
  
  $category = array();
  $q = db_query("SELECT category_id FROM nr_topic_category WHERE topic_id='$tid'");
  while ($a = db_fetch_array($q))
    array_push($category, $a['category_id']);


  $tipoInformacao = array();
   $q = db_query("SELECT type_id FROM topic_type WHERE topic_id=$tid");
   while ($a = db_fetch_array($q))
     array_push($tipoInformacao, $a['type_id']);
}

?>