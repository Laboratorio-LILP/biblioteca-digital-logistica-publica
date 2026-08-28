<?php

// NOU-RAU - Copyright (C) 2002 Instituto Vale do Futuro
// This program is free software; see COPYING for details.
// Editar usuário: /user/edit.php

require_once '../include/start.php';
require_once BASE . 'include/format.php';
require_once BASE . 'include/page_u.php';
require_once BASE . 'include/util.php';
require_once BASE . 'include/util_u.php';
require_once BASE . 'include/util_t.php';



if($_SERVER["REQUEST_METHOD"] == "GET") {
 	$uid = isset($_GET['uid'])?$_GET['uid']:NULL;
}
else {

// filter input
$uid = isset($_POST['uid'])?$_POST['uid']:NULL; 
$username = strtolower(trim($_POST['username']));
$name = trim($_POST['name']);
$email = trim($_POST['email']);
$info = trim($_POST['info']);
$level = $_POST['level'];
$password =  isset($_POST['password'])?$_POST['password']:NULL;
$password2 = isset($_POST['password2'])?$_POST['password2']:NULL;
$acesso = isset($_POST['ckAcesso'])?$_POST['ckAcesso']:NULL;
$sent = $_POST['sent'];

}

// validate access
// exige uma sessão realmente autenticada antes de qualquer coisa; o nível do
// editor vem da sessão, nunca da requisição
if (!isset($_SESSION['suid']) || !isset($_SESSION['slevel']) || !valid_int($_SESSION['suid']))
  redirect("{$cfg_site}user/login.php?url=" . rawurlencode($_SERVER['REQUEST_URI']));

$is_admin = ((int) $_SESSION['slevel'] === ADM_LEVEL);


	// validate input
	if (!valid_opt_int($uid))
	   message("{$cfg_site}user/list.php","Parâmetro Inválido !", "failure");
   
	if (empty($uid)) {
		// handle create mode; criar usuário é operação de administrador
		if (!$is_admin)
	    	message("{$cfg_site}","Acesso Negado !", "failure");
	}
	else {
		// handle edit mode
		if (!$is_admin && (string) $_SESSION['suid'] !== (string) $uid)
	    	message("{$cfg_site}","Acesso Negado !", "failure");

		if (empty($sent)) {
			// first time; load from base
			load();
			form();
		} 
		else if ($sent =="Cancelar") {
			// abort editing
			redirect("{$cfg_site}user/?uid=$uid");
		}
	}  

// validate input
if (empty($sent))
  form();

if (empty($uid)) {
  if (empty($username))
    form(_('Please specify an identification'));
  if (!valid_username($username))
    form("Identificação inválida: use apenas os caracteres indicados");
  if (db_simple_query("SELECT COUNT(id) FROM users WHERE username='$username'"))
    form("Já existe um usuário com a mesma identificação");
  if (empty($password) || empty($password2))
    form("Please specify a password and its confirmation");
  if ($password != $password2) {
    unset($password);
    unset($password2);
    form("Senha de confirmação não corresponde com a senha.");
  }
}

if (empty($name))
  form(_('Please specify the full name'));
if (empty($email))
  form(_('Please specify the e-mail address'));
if (!valid_email($email))
  form("E-mail inválido: verifique");
$n = strlen($info) - $cfg_max_user_info;
if ($n > 0)
  form("O tamanho da informação excedeu o máximo permitido em $n caracteres");

// o nível de acesso só é aceito da requisição quando o editor é administrador;
// na auto-edição preserva-se o nível já gravado para o usuário
if ($is_admin) {
  if (!valid_int((string) $level)
      || !in_array((int) $level, array(USR_LEVEL, MNT_LEVEL, RES_LEVEL, ADM_LEVEL), true))
    form('Por favor escolha um nível de acesso');
  $level = (int) $level;
}
else {
  $level = get_user($uid, 'level');
  // o widget de acesso aos tópicos só existe no formulário do administrador
  $acesso = NULL;
}

// os tópicos vêm da requisição; aceite apenas inteiros
if (!empty($acesso)) {
  foreach ((array) $acesso as $selected) {
    if (!valid_int((string) $selected))
      message("{$cfg_site}user/list.php","Parâmetro Inválido !", "failure");
  }
}

/*if(empty($incluir))
  form('Por favor especifique os tópicos, que o usuário terá acesso');*/

if (!empty($sec) && empty($tid))
  form("Por favor escolha um tópico");

if (empty($uid)) {
  // insert new user
 db_command_params('INSERT INTO users (username,password,name,email,info,level) VALUES ($1,$2,$3,$4,$5,$6)',
                   array($username, rot13($password), $name, $email, $info, $level));
 $uid = db_simple_query("SELECT CURRVAL('users_seq')");
 add_log('c', 'uc', "uid=$uid&from={$_SERVER['HTTP_X_FORWARDED_FOR']}- {$_SERVER['HTTP_USER_AGENT']}");

  foreach($acesso as $selected){
	  db_command_params('INSERT INTO topic_users (users_id,topic_id) VALUES ($1, $2)', array($uid, $selected));
  }
    
	message("{$cfg_site}user/list.php","O Usuário foi criado.", "success");

} else {
	
// update user info
  db_command_params('UPDATE users SET name=$1,email=$2,info=$3, level=$4 WHERE id=$5',
                    array($name, $email, $info, $level, $uid));
  add_log('c', 'uu', "uid=$uid&from={$_SERVER['HTTP_X_FORWARDED_FOR']}- {$_SERVER['HTTP_USER_AGENT']}");
  
	  if(!empty($acesso)){
	  
	  db_command_params('DELETE FROM topic_users WHERE users_id=$1', array($uid));

		foreach($acesso as $selected){
		  db_command_params('INSERT INTO topic_users (users_id,topic_id) VALUES ($1, $2)', array($uid, $selected));
		}	  
  }	  
} 
	
// finish
   message("{$cfg_site}user/?uid=$uid","Dados do Usuário foram atualizdos", "success");



/*-------------- functions --------------*/

// como db_command() só aceita SQL pronto, aqui os valores vão ligados
// (bind) em vez de interpolados na consulta
function db_command_params ($sql, $params)
{
  global $db_conn;

  if (!($q = pg_query_params($db_conn, $sql, $params)))
    fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");

  return @pg_affected_rows($q);
}

function form ($msg = ""){
	global $cfg_site, $cfg_max_user_info;
	global $uid, $username, $password, $password2, $name,$email, $info, $level,  $topic_id, $option, $topico, $opttopicos, $incluir, $excluir;

	page_begin();
		
	if (empty($uid))
		echo html_h('Registrar novo Usuário');
	else
		echo html_h('Editar Usuário:' . ' '. $username);
	
	format_warning($msg);
	
	$topicos = carrega_topicos();
    //html_form_begin($PHP_SELF);
  
    echo "<div class=\"form_box\">";
	 
    echo "<form name='formuser' enctype='multipart/form-data' method='post' action='".$_SERVER['PHP_SELF']."' >";

	if (empty($uid)) {
		/*html_form_hidden('code', $code);*/
		html_form_text("Identificação", 'username', 20, $username, 20, true, 'Digite  a identificação', "Use apenas letras e números. Pode ser usados '-', '_' ou '.' como separadores se necessário.");
		echo "<p>\n";
		html_form_password("Senha", 'password', 10, $password, 10, true, 'Digite a senha');
		echo "<p>\n";
		html_form_password("Confirmação da Senha", 'password2', 10, $password2, 10, true, 'Digite a senha novamante' );
		echo "<p>\n";
	}
	else {
		html_form_hidden('uid', $uid);
		html_form_hidden('username', $username);
	}
	
	html_form_text('Nome completo', 'name', 80, $name, 100,true, 'Digite o nome completo do usuário');
	echo "<p>\n";
	html_form_text(_('E-mail'), 'email', 50, $email, 50, true, 'Digite o e-mail usuário');
	echo "<p>\n";
   	html_form_area('Informações', 'info', 4, $info, $cfg_max_user_info, false, 'Digite as informação sobre usuário');
	echo "<p>\n";

    ?>
    <script type="text/javascript"> 
	$(document).ready(function() {
		$('#ajuda a').each(function() {
			var $link = $(this);
			var $dialog = $('<div></div>')
				.load($link.attr('href'))
				.dialog({
					autoOpen: false,
					modal:true,
					title: $link.attr('title'),
					width: 800
					
				});
 
			$link.click(function() {
				$dialog.dialog('open');
				return false;
			});
			return false;
		});
	});
	</script> 
<?php
  

	if (is_administrator()){

		$default = (!empty($level)?$level:1);

        $optuser = array (1=>"Colaborador ou Depositante", 2=>"Curador e Publicador" , 3=>"Responsável", 4=>"Administrador");
		
		html_form_radio('Nível de Acesso', 'level', $optuser, $default,"<a href=\"{$cfg_site}user/ajudanivel.php\" title=\"Nível de Acesso\"> <i class=\"bx bxs-message-rounded-detail\"></i></a>");
		
        
    	if (empty($uid))
    	  $uid = 0;

       //Carrega um array com os tópicos que o usuario tem direito
 	     $sql = "SELECT topic.id, topic.name, topic.parent_id FROM users INNER JOIN (topic_users INNER JOIN topic ON topic_id = topic.id) ON users.id = users_id WHERE users_id =".	$uid." ORDER BY topic.id";
		$resulttopic = db_query($sql);
		
		if (db_rows($resulttopic)) {
			while ($qtopic = db_fetch_array($resulttopic)){
				$opttopicos[$qtopic['id']] = $qtopic['name'];
			}
		}
  	
	   echo "</br>";
       echo "<p>\n";
       echo "<label for=\"$name\">Acesso aos Tópicos:</label>\n";
	   echo "</br>";
	   
	   //echo "<input id='alladicionar' type='checkbox' name='alladicionar' onClick=\"selecionartodos('ckAcesso[]');\">Selecionar todos <br />";
       
	   echo  "<p><input type=\"button\" id=\"alladicionar\" value=\"Selecionar todos\" onClick=\"selecionartodos('ckAcesso[]');\"></p>";
	  
	   
	  foreach ($topicos as $topico){
		   
		   $class = "atopic".$topico[1]; 
		   
		   if (count((array)$opttopicos)!=0) 
				$checked = (array_key_exists($topico[0] ,$opttopicos)?"Checked":"");
			else 
			 $checked = '';
		 
             echo "<span class=\"{$class}\" ><input type=\"checkbox\"  name=\"ckAcesso[]\" value=\"{$topico[0]}\" {$checked}> $topico[2]</span>\n";
		 echo "<br>";
      }
		
	echo "</p>\n";


}	
 else {
   	  html_form_hidden('level', $level);
	  
 }
	 
 

	if (empty($uid)) {
		echo "<div class=\"botao\">";
		html_form_submit('Salvar', 'sent');
		echo "</div>";
		
	} else {
		echo "<div class=\"botao\">";
		html_form_submit('Salvar', 'sent');
		echo "</div>";
		echo "<div class=\"botao\">";
		html_form_submit('Cancelar', 'sent', false);
		echo "</div>";
	}
	html_form_end();
	echo "<p>\n";
	echo "</div>\n";

    page_end();
	exit();
}

function load ()
{
  global $uid, $username, $name, $email, $info, $level, $topic_id, $options;

  $a = get_user($uid);

  $username = $a['username'];
  $name = $a['name'];
  $email = $a['email'];
  $info = $a['info'];
  $level = $a['level'];
  $topic_id = $a['topic_id'];
  $options = $a['options'];
  
}

function carrega_topicos(){

 global $db_conn;
 $topico = array();

 $topic = db_query("SELECT id, name FROM topic WHERE parent_id = 0 ORDER BY name");

 while ($q = db_fetch_array($topic)){
	//$topico[$q['id']] = $q['name'];
	$topico[]=array($q['id'],0,$q['name']);
 	$resulttopic = db_query("SELECT id, name From topic where parent_id =".$q['id']." order by name");
 	while ($qtopic = pg_fetch_array($resulttopic)){
		$topico[]=array($qtopic['id'],1,$qtopic['name']);
 	 	//$topico[$qtopic['id']] = $qtopic['name'];
 	 	$resulttopic1 = db_query("SELECT id, name From topic where parent_id =".$qtopic['id']." order by name");
 	    while ($qtopic1 = pg_fetch_array($resulttopic1)){
 			//$topico[$qtopic1['id']] = $qtopic1['name'];
			$topico[]=array($qtopic1['id'],2,$qtopic1['name']);
 		    $resulttopic2 = db_query("SELECT id, name From topic where parent_id =".$qtopic1['id']." order by name");
 			while ($qtopic2 = pg_fetch_array($resulttopic2)){
				$topico[]=array($qtopic2['id'],3,$qtopic2['name']);
		       // $topico[$qtopic2['id']] = $qtopic2['name'];
 				$resulttopic3 = db_query("SELECT id, name From topic where parent_id =".$qtopic2['id']." order by name");
 				while ($qtopic3 = pg_fetch_array($resulttopic3)){
					//$topico[$qtopic3['id']] = $qtopic3['name'];
					$topico[]=array($qtopic3['id'],4,$qtopic3['name']);
 				}
 			}
 		}
 	}
 }

 return $topico;
}

?>
