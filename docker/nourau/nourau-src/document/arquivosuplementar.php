<?php

// NOU-RAU - Copyright (C) 2002 Instituto Vale do Futuro
// This program is free software; see COPYING for details.

require_once '../include/start.php';
require_once BASE . 'include/html.php';
require_once BASE . 'include/control.php';
require_once BASE . 'include/defs_d.php';
require_once BASE . 'include/format.php';
require_once BASE . 'include/page_d.php';
require_once BASE . 'include/util.php';
require_once BASE . 'include/util_d.php';

global $cid, $did, $op, $id, $filename, $tid;

html_header(_('Arquivos Suplementares'), "", "", false);


 if($_SERVER["REQUEST_METHOD"] == "POST") {
      
	  $sent = $_POST['sent'];	
      $op = $_POST['op'];
	  $id = $_POST['id'];
	  $tid = $_POST['tid'];	  
	  $did = $_POST['did'];	  
	  $status = $_POST['status'];
    }
 else {
      $op = $_GET['op'];
	  $did = $_GET['did']; 
	  $tid = $_GET['tid'];
	  $id = isset($_GET['id'])?$_GET['id']:0;
	  $status = $_GET['status'];
 }
	
// validate input
if (!valid_int($did))
   message($cfg_site,"Parâmetro inválido", "failure");	

// check access rights
  check_user_rights();

/* O alvo da operação é resolvido no banco, não no pedido: do cliente vem apenas
   um id (o do anexo, em op='d'; o do documento, nos demais casos). Documento,
   coleção, situação, formato e caminho em disco saem sempre da linha carregada
   aqui - nunca de $_POST/$_GET. */
if ($op == 'd')
   $sf = sf_load_file($id);
else
   $sf = sf_load_document($did);

// controle de acesso real, avaliado sobre a coleção resolvida no banco
sf_check_topic_rights($sf);

$did    = (int) $sf['document_id'];
$tid    = (int) $sf['topic_id'];
$id     = (int) $sf['sf_id'];
$status = $sf['status'];

if (empty($sent)) {
	form();
}
else if ($sent == 'Sim' || $sent == 'Salvar') {
 
	
	if ($op == 'd'){

		//Apaga o arquivo suplementar
  	
		$format_id = (int) $sf['format_id'];
	
       //Apaga o fisicamnete arquivo anterior
	   $qDel = pg_query_params($db_conn, 'SELECT extension,compress FROM nr_format WHERE id = $1', array($format_id));
	   if ($qDel === false)
	      fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");
	   $aDel = pg_fetch_array($qDel);
	   /* $id e $tid já são inteiros vindos do banco; a extensão é reduzida a
	      alfanuméricos para que o caminho não possa sair do diretório configurado */
	   $extDel = preg_replace('/[^A-Za-z0-9]/', '', isset($aDel['extension']) ? $aDel['extension'] : '');
	   
	   if ($status == 'i' ||$status == 'w') {
		   $fDel = "$cfg_dir_incoming/S"."$id.$extDel";
		   if ($aDel['compress'] == 'y')
				$fDel .= '.gz';
		   
          @unlink($fDel);   
       }  
       else { 
	   
	   	   $fDel = "$cfg_dir_archive/$tid/S"."$id.$extDel";
			if ($aDel['compress'] == 'y')
				$fDel .= '.gz';
			@unlink($fDel);
	   }
     
       if (pg_query_params($db_conn, 'DELETE FROM supplementary_files WHERE id = $1', array($id)) === false)
          fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");
	}
	else if ($op == 'i'){
		
		if (file_exists($_FILES['file']['tmp_name'])) {
			$file = $_FILES["file"]["tmp_name"];
			$file_type = $_FILES["file"]["type"];
			$file_name = trim($_FILES['file']['name']);
			$file_size = $_FILES["file"]["size"];
			$parts = explode('.',$file_name);
			$file_ext = end($parts);
			list('fid' => $fid, 'cid' => $cid) = find_format($file_type);
		}
		
		if (empty($sent))
		  form();
	  
		if (!$fid){
	    	form("O tipo de arquivo não é aceito nesta coleção.");
		}
        
       //  insert supplementary document
		if (pg_query_params($db_conn, 'INSERT INTO supplementary_files (filename,size,document_id,category_id,format_id, owner_id, topic_id) values ($1,$2,$3,$4,$5,$6,$7)',
		                    array($file_name, $file_size, $did, $cid, $fid, $_SESSION['suid'], $tid)) === false)
		   fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");
		$id = (int) db_simple_query("SELECT CURRVAL('supplementary_files_seq')");
		//Grava o arquivo no servidor
		$qSave = db_query("SELECT extension,compress FROM nr_format WHERE id=".(int) $fid);
		$aSave = db_fetch_array($qSave);
		/* $id e $tid são inteiros; a extensão é reduzida a alfanuméricos para
		   que o caminho não possa sair do diretório configurado */
		$extSave = preg_replace('/[^A-Za-z0-9]/', '', isset($aSave['extension']) ? $aSave['extension'] : '');
		
       
	   if ($status == 'i' ||$status == 'w') {
           chmod($file, 0644);
		   $new = "$cfg_dir_incoming/S"."$id.$extSave";
           copy($file, $new); 
		   
		   if ($aSave['compress'] == 'y') {
				// verifica se o arquivo compacta existe para apaga-lo
				$filecompact = $new. '.gz';
				//compacta o arquivo
				exec("gzip -9 $new");
			}
		   
       }  
       else { 
            chmod($file, 0644);
			$new = "$cfg_dir_archive/$tid/S"."$id.$extSave";

			copy($file, $new);
   
			if ($aSave['compress'] == 'y') {
				// verifica se o arquivo compacta existe para apaga-lo
				$filecompact = $new. '.gz';
				//compacta o arquivo
				exec("gzip -9 $new");
			}
	   }

	}
	
	//add_log('n', 'di', "did=$did&from=$REMOTE_ADDR $HTTP_USER_AGENT");
	
	echo "<script language='JavaScript'>";
    echo "arquivosuplementar($did,$tid);";
    echo "setTimeout('window.close();', 100);";
    echo "</script>";
	
}
else if ($sent == "Cancelar" || $sent =="Não" ) {
  // abort editing
   echo "<script language='JavaScript'>";
   echo "setTimeout('window.close();', 100);";
   echo "</script>";
  exit();
}

/* Carrega o anexo pelo id e traz junto o documento a que ele pertence.
   É a única forma de identificar o alvo de op='d'. */
function sf_load_file ($sfid)
{
  global $cfg_site, $db_conn;

  if (!valid_int($sfid))
    message($cfg_site,"Parâmetro inválido", "failure");

  $q = pg_query_params($db_conn,
       'SELECT S.id AS sf_id, S.filename, S.format_id, D.id AS document_id,' .
       ' D.topic_id, D.owner_id, D.status' .
       ' FROM supplementary_files S INNER JOIN nr_document D ON S.document_id = D.id' .
       ' WHERE S.id = $1', array($sfid));
  if ($q === false)
    fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");
  if (!pg_num_rows($q))
    message($cfg_site,"Arquivo não encontrado", "failure");
  return pg_fetch_array($q);
}

/* Carrega o documento pelo id, para as operações que ainda não têm anexo. */
function sf_load_document ($did)
{
  global $cfg_site, $db_conn;

  if (!valid_int($did))
    message($cfg_site,"Parâmetro inválido", "failure");

  $q = pg_query_params($db_conn,
       'SELECT id AS document_id, topic_id, owner_id, status FROM nr_document WHERE id = $1',
       array($did));
  if ($q === false)
    fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");
  if (!pg_num_rows($q))
    message($cfg_site,"Documento não encontrado", "failure");
  $a = pg_fetch_array($q);
  $a['sf_id']    = 0;  // nenhum anexo selecionado
  $a['filename'] = '';
  $a['format_id'] = 0;
  return $a;
}

/* Autorização do endpoint, avaliada sobre a coleção do documento resolvido no
   banco. Espelha a regra de edição do documento (document/edit.php,
   document/index.php e document/action.php): administrador; curador ou
   responsável inscrito na coleção do documento (topic_users, como em
   check_maintainer_rights/check_topic_users_edit); ou o próprio depositante,
   enquanto o documento ainda está em curadoria (status 'i' ou 'w'), como diz
   document/index.php ("O depositante pode editar apenas os documentos que ele
   inserir que estão em aprovação").
   A sessão é lida direto de $_SESSION e a inscrição é conferida direto em
   topic_users para que esta página não dependa de include/control.php. */
function sf_check_topic_rights ($row)
{
  global $cfg_site, $db_conn;

  $slevel = isset($_SESSION['slevel']) ? (int) $_SESSION['slevel'] : 0;
  $suid   = isset($_SESSION['suid']) ? $_SESSION['suid'] : '';

  if (!valid_int($suid) || $slevel < USR_LEVEL)
    message($cfg_site,"Acesso negado", "failure");

  if ($slevel >= ADM_LEVEL)
    return;

  if ($slevel == MNT_LEVEL || $slevel == RES_LEVEL) {
    $q = pg_query_params($db_conn,
         'SELECT 1 FROM topic_users WHERE topic_id = $1 AND users_id = $2',
         array($row['topic_id'], $suid));
    if ($q !== false && pg_num_rows($q) > 0)
      return;
    message($cfg_site,"Acesso negado", "failure");
  }

  if ($slevel == USR_LEVEL && (int) $row['owner_id'] === (int) $suid &&
      ($row['status'] == 'i' || $row['status'] == 'w'))
    return;

  message($cfg_site,"Acesso negado", "failure");
}

function find_format ($file_type)
{
  $type = explode('/', $file_type);
 $format_id = 0;
  $q = db_query("SELECT C.id,C.type,C.subtype FROM nr_format C,nr_category_format CC WHERE  CC.format_id=C.id");
  while ($a = db_fetch_array($q)) {
    if ($a['type'] == 'any') {
      // match against all types
      $q2 = db_query("SELECT id,type,subtype FROM nr_format WHERE subtype<>'any'");
      while ($a2 = db_fetch_array($q2))
        if (!strcasecmp($a2['type'], $type[0]) &&
            !strcasecmp($a2['subtype'], $type[1])) {
          $format_id = $a2['id'];
          break;
        }
		
    }
    else if ($a['subtype'] == 'any') {
      // match against all subtypes with the given type
      $q2 = db_query("SELECT id,type,subtype FROM nr_format WHERE type='{$a['type']}' AND subtype<>'any'");
      while ($a2 = db_fetch_array($q2))
        if (!strcasecmp($a2['type'], $type[0]) &&
            !strcasecmp($a2['subtype'], $type[1])) {
          $format_id = $a2['id'];
          break;
        }
    }
    else {
      // match against specified type and subtype
      if (!strcasecmp($a['type'], $type[0]) &&
          !strcasecmp($a['subtype'], $type[1]))
        $format_id = $a['id'];  
      }
	
    if ($format_id)
      break;
  }
  
  if ($format_id > 0) {
   
    $q = db_query("SELECT category_id FROM  nr_category_format  WHERE  format_id=".$format_id );
	$a = db_fetch_array($q);
    $category_id = $a['category_id'];	
  }
  else {
    $format_id = 0; 
	$category_id = 0;
  }	  

  return ['fid' => $format_id, 'cid' =>  $category_id ];
}


function form ($msg = ""){
	global $cfg_site;
	global $cid, $did, $op, $id, $tid, $status, $sf;
	
	echo "<div class='arqsuplementar'>";

	if ($op == 'i') {
		echo html_h(html_b('Adicionar Anexo'));
		format_warning($msg);
		
		echo "<br>";

		html_form_begin("{$_SERVER['PHP_SELF']}", true, 'multipart/form-data');
		
		html_form_file('Documento', 'file', true, "Selecione o arquivo.", true);
		

    	echo "<input type='hidden' name='did' value=$did>";
		echo "<input type='hidden' name='op' value=$op>";
		echo "<input type='hidden' name='tid' value=$tid>";
		echo "<input type='hidden' name='id' value=$id>";
		echo "<input type='hidden' name='status' value=$status>";

	   echo "<div class=\"botao\">";
		html_form_submit('Salvar', 'sent');
		echo "</div>";
		echo "<div class=\"botao\">";
		html_form_submit('Cancelar', 'sent', false);
		echo "</div>";
	
	}
    else if ($op == 'd') {

     echo html_h("Excluir Anexo");

     // o anexo já foi carregado e autorizado acima; nada aqui vem do pedido
	 $a = $sf;

   
     $msg = "Você deseja remover o arquivo ". $a['filename']. "?";

	 echo "<form method='post' action='".$_SERVER['PHP_SELF']."'>";
	 echo "<input type='hidden' name='did' value=$did>";
	 echo "<input type='hidden' name='op' value=$op>";
	 echo "<input type='hidden' name='tid' value=$tid>";
	 echo "<input type='hidden' name='id' value=$id>";
	 echo "<input type='hidden' name='format_id' value={$a['format_id']}>";
	 echo "<input type='hidden' name='status' value=$status>";



       echo "<div class=\"botao\">";
		html_form_submit('Sim', 'sent');
		echo "</div>";
		echo "<div class=\"botao\">";
		html_form_submit('Não', 'sent', false);
		echo "</div>";

	
    }
	
  echo "</div>";
  html_footer();
  exit();
}

?>
