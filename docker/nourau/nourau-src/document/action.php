<?php

// NOU-RAU - Copyright (C) 2002 Instituto Vale do Futuro
// This program is free software; see COPYING for details.
//document action: /document/action.php

require_once '../include/start.php';
require_once BASE . 'include/defs_d.php';
require_once BASE . 'include/util_d.php';


/*-------------- consultas com parâmetros ligados --------------*/

// include/db.php só aceita SQL já montada; para ligar valores é preciso
// pg_query_params(). A conexão é a mesma global usada por include/db.php.

function nr_query_params ($sql, $params)
{
  global $db_conn;

  if (!($q = pg_query_params($db_conn, $sql, $params)))
    fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");
  return $q;
}

function nr_command_params ($sql, $params)
{
  global $db_conn;

  if (!pg_query_params($db_conn, $sql, $params))
    fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");
}


/*-------------- controle de acesso desta ação --------------*/

// Os auxiliares de include/control.php testam $_SESSION['session'], que não é
// atribuído em nenhum ponto da árvore, e por isso liberam acesso indevidamente.
// As funções abaixo não dependem deles: leem $_SESSION['suid']/$_SESSION['slevel']
// diretamente e resolvem a coleção sempre pelo registro do documento.

function nr_session_level ()
{
  return isset($_SESSION['slevel']) ? (int) $_SESSION['slevel'] : 0;
}

function nr_session_uid ()
{
  return (isset($_SESSION['suid']) && valid_int($_SESSION['suid'])) ? (int) $_SESSION['suid'] : 0;
}

// Encerra a requisição: visitante anônimo vai para o login, autenticado sem
// direito recebe recusa. Tanto redirect() quanto message() terminam o script.
function nr_deny_access ()
{
  global $cfg_site;

  if (nr_session_uid() < 1)
    redirect("{$cfg_site}user/login.php?url=" . rawurlencode($_SERVER['REQUEST_URI']));
  message($cfg_site, "Acesso negado", "failure");
}

function nr_is_administrator ()
{
  return nr_session_level() == ADM_LEVEL;
}

// Curador/responsável vinculado à coleção do documento (tabela topic_users).
function nr_is_topic_curator ($tid)
{
  $level = nr_session_level();
  $uid   = nr_session_uid();

  if ($uid < 1 || ($level != MNT_LEVEL && $level != RES_LEVEL))
    return false;
  if (!valid_int($tid) || (int) $tid < 1)
    return false;

  $q = nr_query_params('SELECT 1 FROM topic_users WHERE topic_id=$1 AND users_id=$2',
                       array((int) $tid, $uid));
  return db_rows($q) > 0;
}

// Porteiro das operações de curadoria (aprovar, rejeitar, remover, trocar de
// coleção): administrador, ou curador/responsável da coleção do documento.
function nr_check_curator_rights ($tid)
{
  if (nr_is_administrator() || nr_is_topic_curator($tid))
    return;
  nr_deny_access();
}

function nr_check_administrator_rights ()
{
  if (nr_is_administrator())
    return;
  nr_deny_access();
}

// Descarte de documento ainda em elaboração: o próprio depositante, além do
// curador da coleção e do administrador.
function nr_check_discard_rights ($tid, $owner_id)
{
  $uid = nr_session_uid();

  if ($uid > 0 && valid_int($owner_id) && (int) $owner_id === $uid)
    return;
  nr_check_curator_rights($tid);
}


if(isset($_GET)) {
	
 if (isset($_GET['op']))
 	$op = $_GET['op'];

 if (isset($_GET['did']))
 	$did =  $_GET['did'];	

if (isset($_GET['tidold']))
		$tidold = $_GET['tidold'];
	
	if (isset($_GET['tid']))
		$tid = $_GET['tid'];
	
}


if(isset($_POST)) {
	
	if (isset($_POST['conf']))
		$conf = $_POST['conf'];

	if (isset($_POST['did']))
		$did = $_POST['did'];
	 
	if (isset($_POST['op']))
		$op = $_POST['op'];
	
	if (isset($_POST['tidold']))
		$tidold = $_POST['tidold'];
	
	if (isset($_POST['tid']))
		$tid = $_POST['tid'];

} 
  

// validate input
if (!valid_int($did))
   message("{$cfg_site}document/?code=" . rawurlencode($a['code']),"Parâmetro Inválido !", "failure");

$did = (int) $did;

$a = get_document($did);

// coleção do documento: vem sempre do registro, nunca da requisição
$doc_tid = (int) $a['topic_id'];

if ($op == 'v') { // ---------------- accept document after verification
  //validate access
  nr_check_administrator_rights();
   check_administrator_rights();
  check_user_rights();
  if ($a['status'] != 'v')
    error('Acesso Negado');
  if (substr($a['code'],0,4)!='vtls') {
      // update document
      nr_command_params('UPDATE nr_document SET status=\'w\' WHERE id=$1', array($did));
      add_log('n', 'dv', "did=$did");

      // notify maintainer
      $title = $a['title'];
      $topic = get_topic($a['topic_id'], 'name');
      $email = get_user($a['owner_id'], 'email');
      send_mail($email, _('Document received'), _M("The document with title '@1' was received on the topic '@2'.", $title, $topic));
  }
  else { // tese - arquivar imediatamente
      // move file to archive, renaming it and compressing if necessary
      $q2 = db_query("SELECT extension,compress FROM nr_format WHERE id='{$a['format_id']}'");
      $a2 = db_fetch_array($q2);
      $old = "$cfg_dir_incoming/{$a['filename']}";
      if (!file_exists("$cfg_dir_archive/$doc_tid"))
        mkdir("$cfg_dir_archive/$doc_tid");
      $new = "$cfg_dir_archive/$doc_tid/$did.{$a2['extension']}";
      $filename = substr($a['filename'], 5); // remove random prefix
      if (!@rename($old, $new))
	  error(_('Rename failed')); // FIXME: notify admin?
      if ($a2['compress'] == 'y') {
	  // compress it
	  exec("gzip -9 $new");
      }

      // update document
      nr_command_params('UPDATE nr_document SET status=\'a\',filename=$1,visits=\'0\',downloads=\'0\' WHERE id=$2',
                        array($filename, $did));
      add_log('n', 'dv', "did=$did");

      // add document to search index
      nr_command_params('INSERT INTO nr_document_queue (op,document_id) VALUES (\'i\',$1)', array($did));

      // notify owner
      $title = $a['title'];
      $topic = get_topic($a['topic_id'], 'name');
      $email = get_user($a['owner_id'], 'email');
      send_mail($email, _('Document accepted'), _M("The document with title '@1' has been accepted in the topic '@2'.", $title, $topic));
  }
  // finish
  message(_('Document accepted'), "{$cfg_site}document/manage.php");
}
else if ($op == 'a') { // ---------------- approve document
  	// validate access
  	 $tid = $doc_tid;
  	nr_check_curator_rights($doc_tid);
  	check_maintainer_rights($tid);

	if ($a['status'] != 'w') {
    	  print "acesso_negado";
    	  exit();
	}

  	// ask confirmation
  	if (empty($conf)) {
    	$title = $a['title'];
    	remove("Você deseja aprovar o documento com título $title ?", "{$_SERVER['PHP_SELF']}?did=$did&op=$op", false);
  	}

 	if ($conf == 'Sim') {

		if ($a['remote'] == 'n') {	 
		
		if (strlen($a['filename']) > 0 ) {   
			// move file to archive, renaming it and compressing if necessary
			$q2 = db_query("SELECT extension,compress FROM nr_format WHERE id='{$a['format_id']}'");
			$a2 = db_fetch_array($q2);
			$old = "$cfg_dir_incoming/{$a['filename']}";
			
			//echo "$cfg_dir_archive/$doc_tid";

		
		
			if (!file_exists("$cfg_dir_archive/$doc_tid"))
				mkdir("$cfg_dir_archive/$doc_tid");
	

			$new = "$cfg_dir_archive/$doc_tid/$did.{$a2['extension']}";
			$filename = substr($a['filename'], 5); // remove random prefix
		

			if (file_exists($old)) 
				rename($old, $new);
			else {
				print "error";
				exit (); 
			}
			
			if ($a2['compress'] == 'y') 
				// compress it
				exec("gzip -9 $new");
			
			/*Arquivos Anexos*/
						
			$qsf = nr_query_params('SELECT * FROM supplementary_files WHERE document_id=$1', array($did));
				
			if (db_rows($qsf)>=1){

				nr_command_params('UPDATE supplementary_files SET topic_id = $1 WHERE document_id=$2', array($tid, $did));
			
				while ($asf = db_fetch_array($qsf)){
							
					$qformat = db_query("SELECT extension,compress FROM nr_format WHERE id='{$asf['format_id']}'");
					$asf2 = db_fetch_array($qformat);
					$old = "$cfg_dir_incoming/S{$asf['id']}.{$asf2['extension']}";
									
					if ($asf2['compress'] == 'y')
						$old .= '.gz';
										
					$new = "$cfg_dir_archive/$doc_tid/S{$asf['id']}.{$asf2['extension']}";
					if ($asf2['compress'] == 'y')
					$new .= '.gz';	
									
					//echo "<br>$old<br>$new"; 
					//exit();
									
					if(file_exists($old))	
					rename($old, $new);
					else{
						print 'error' ;
						exit();
					}										
								
				}
			}		
		} else{
				print 'error_arquivo' ;
			exit();
		}

		} else {
			$filename =  $a['acesso_eletronico'];
		}
  
   nr_command_params('UPDATE nr_document SET status=\'a\',filename=$1,visits=\'0\',downloads=\'0\' WHERE id=$2',
                     array($filename, $did));
   add_log('n', 'dv', "did=$did");
   print "sucesso";
 }
  else
    redirect("{$cfg_site}document/manage.php"); 
}
else if ($op == 'r') { // ---------------- reject document
  // validate access
  $tid = $doc_tid;
  nr_check_curator_rights($doc_tid);
  check_maintainer_rights($tid);
  if ($a['status'] != 'v' && $a['status'] != 'w') {
    print "error";
    exit();
  }

  // ask confirmation
  if (empty($conf)) {
    $title = $a['title'];
    remove("Você deseja rejeitar o documento com título ' $title ' ?", "{$_SERVER['PHP_SELF']}?did=$did&op=$op", false);
  }

  if ($conf == 'Sim') {
	  
	if ($a['remote'] == 'n') {	  
		// remove file and document entry
		//@unlink("$cfg_dir_incoming/{$a['filename']}");
		
		//$qsf = db_query("SELECT * FROM supplementary_files WHERE document_id=$did");
			
		//		  if (db_rows($qsf)>=1){
		//			db_command("UPDATE supplementary_files SET topic_id = $tid WHERE document_id=$did");
					
		//				while ($asf = db_fetch_array($qsf)){
							
		//						$qformat = db_query("SELECT extension,compress FROM nr_format WHERE id='{$asf['format_id']}'");
		//						$asf2 = db_fetch_array($qformat);
		//						$old = "$cfg_dir_incoming/S{$asf['id']}.{$asf2['extension']}";
								
		//						if ($asf2['compress'] == 'y')
		//							$old .= '.gz';
									
		//						$new = "$cfg_dir_archive/{$a['topic_id']}/S{$asf['id']}.{$asf2['extension']}";
		//						if ($asf2['compress'] == 'y')
		//							  $new .= '.gz';	
								  
								// echo "<br>$old<br>$new"; 
									
		//						if (!@rename($old, $new))
		//						  print 'error' ;
	         //					}	 
		//		}	
	}
    nr_command_params('DELETE FROM nr_document WHERE id=$1', array($did));
    add_log('n', 'dr', "did=$did");

     print "sucesso";
 
    // finish
   // message("Dcoumento Rejeitado", "{$cfg_site}document/manage.php");
  }
  else
    redirect("{$cfg_site}document/manage.php");
}
else if ($op == 'd') { // ---------------- remove document
  // validate access
  nr_check_curator_rights($doc_tid);
  if ($a['status'] != 'a') {
    print "error";
    exit();
  }

  // ask confirmation
  if (empty($conf)) {
    $title = $a['title'];
    remove(" Você deseja remover o documento com título: ' $title ' ?" , "{$_SERVER['PHP_SELF']}?did=$did&op=$op", true);
  }

  if ($conf == 'Sim') {
	 
  if ($a['remote'] == 'n') {
   // remove file and document entry
    $q2 = db_query("SELECT extension,compress FROM nr_format WHERE id='{$a['format_id']}'");
    $a2 = db_fetch_array($q2);
    $file = "$cfg_dir_archive/$doc_tid/$did.{$a2['extension']}";
    
	
		if ($a2['compress'] == 'y')
			$file .= '.gz';
   
		$new = "$cfg_dir_remove/$did.{$a2['extension']}";
		if ($a2['compress'] == 'y')
			$new .= '.gz';
    

		if (!@rename($file, $new))
			//	error(_('Rename failed')); // FIXME: notify admin?
		    print 'error' ;
		
      
    //@unlink($file);
   

    // remove document from search index
    //db_command("INSERT INTO nr_document_queue (op,document_id,flag) VALUES ('d','$did',0)");

	//Remove os arquivos suplementares
	 $qsf = nr_query_params('SELECT * FROM supplementary_files WHERE document_id=$1', array($did));
  		if (db_rows($qsf)>=1){
  			while ($asf = db_fetch_array($qsf)){
			 	$qformat = db_query("SELECT extension,compress FROM nr_format WHERE id='{$asf['format_id']}'");
   			    $asf2 = db_fetch_array($qformat);
   				$file = "$cfg_dir_archive/{$asf['topic_id']}/S{$asf['id']}.{$asf2['extension']}";
				
    			if ($asf2['compress'] == 'y')
      		 		$file .= '.gz';
					
				$new = "$cfg_dir_remove/S{$asf['id']}.{$asf2['extension']}";
       			 if ($asf2['compress'] == 'y')
        			  $new .= '.gz';	
					
    		   if (!@rename($file, $new))
				     print 'error' ;
			     
			  //@unlink($file);
    		  nr_command_params('DELETE FROM supplementary_files WHERE id = $1', array($asf['id']));
		  }
		}
	}	
	
	 nr_command_params('UPDATE nr_document SET status=\'d\', updated=\'NOW\' WHERE id=$1', array($did));
    add_log('n', 'dd', "did=$did");

   print "sucesso";
   
  }
  else
    redirect("{$cfg_site}document/?code=" . rawurlencode($a['code']));
}
else if ($op == 't') { // ---------------- Troca de Tópico 
  
  // validate access
  nr_check_curator_rights($doc_tid);
  if ($a['status'] != 'a' ){
	   print 'error';
	   exit();
  }

  // os identificadores de coleção viram componentes de caminho: só inteiros
  if (!valid_int($tid) || !valid_int($tidold) || (int) $tid < 1 || (int) $tidold < 1) {
	   print 'error';
	   exit();
  }
  $tid = (int) $tid;
  $tidold = (int) $tidold;
  
	// update document
		if($tidold != $tid){

  		
		if ($a['remote'] == 'n') {
			
			// move file to the new topic
			 $q2 = db_query("SELECT extension,compress FROM nr_format WHERE id='{$a['format_id']}'");
			 $a2 = db_fetch_array($q2);

			 $old = "$cfg_dir_archive/$tidold/$did.{$a2['extension']}";
			 if ($a2['compress'] == 'y')
				$old .= '.gz';

           

			 if (!file_exists("$cfg_dir_archive/$tid"))
				mkdir("$cfg_dir_archive/$tid");

			 $new = "$cfg_dir_archive/$tid/$did.{$a2['extension']}";
			  if ($a2['compress'] == 'y')
				$new .= '.gz';
			 
			   
			 if (!@rename($old, $new))
			   print 'error'; 
			/* else 
			   @unlink($old);*/
			  
			 /*Arquivos Anexos*/
					
			  $qsf = nr_query_params('SELECT * FROM supplementary_files WHERE document_id=$1', array($did));
			
				  if (db_rows($qsf)>=1){
					nr_command_params('UPDATE supplementary_files SET topic_id = $1 WHERE document_id=$2', array($tid, $did));
					
						while ($asf = db_fetch_array($qsf)){
							
								$qformat = db_query("SELECT extension,compress FROM nr_format WHERE id='{$asf['format_id']}'");
								$asf2 = db_fetch_array($qformat);
								$old = "$cfg_dir_archive/$tidold/S{$asf['id']}.{$asf2['extension']}";
								
								if ($asf2['compress'] == 'y')
									$old .= '.gz';
								
									
								$new = "$cfg_dir_archive/$tid/S{$asf['id']}.{$asf2['extension']}";
								if ($asf2['compress'] == 'y')
									  $new .= '.gz';	
								  							
								if (!@rename($old, $new))
								  print 'error' ;
								//else 			  
								//  @unlink($old);
						}	 
				}	
		}
		
		
		   nr_command_params('UPDATE nr_document SET topic_id = $1, updated=\'now\' WHERE id=$2', array($tid, $did));
		   add_log('n', 'du', "did=$did");

            $code = get_document($did, 'code');
			
			/*atualiza a colecao na tabela de visitas e download */
			 $update = 'UPDATE visitas_downloads SET topic_id = $1  WHERE code = $2';
	         nr_command_params($update, array($tid, $code));
	      
		  print 'sucesso';
  

    }
	else
	      print 'error';
}
else if ($op == 'dc') {
  nr_check_discard_rights($doc_tid, $a['owner_id']);
  check_user_rights();
 /*Descartat documento*/
 // validate access
  if ($a['status'] != 'i' ){
    print 'error';
    exit();
  }
 if ($conf == 'Sim') {
	  
	/*if ($a['remote'] == 'n') {	  
		// remove file and document entry
		//@unlink("$cfg_dir_incoming/{$a['filename']}");
		
		/*$qsf = db_query("SELECT * FROM supplementary_files WHERE document_id=$did");
			
				  if (db_rows($qsf)>=1){
					db_command("UPDATE supplementary_files SET topic_id = $tid WHERE document_id=$did");
					
						while ($asf = db_fetch_array($qsf)){
							
								$qformat = db_query("SELECT extension,compress FROM nr_format WHERE id='{$asf['format_id']}'");
								$asf2 = db_fetch_array($qformat);
								$old = "$cfg_dir_incoming/S{$asf['id']}.{$asf2['extension']}";
								
								if ($asf2['compress'] == 'y')
									$old .= '.gz';
									
								$new = "$cfg_dir_archive/{$a['topic_id']}/S{$asf['id']}.{$asf2['extension']}";
								if ($asf2['compress'] == 'y')
									  $new .= '.gz';	
								  
								// echo "<br>$old<br>$new"; 
									
								if (!@rename($old, $new))
								  print 'error' ;
	         					}	 
				}	
	}*/
    nr_command_params('DELETE FROM nr_document WHERE id=$1', array($did));
    add_log('n', 'dr', "did=$did");

     print "sucesso";
 
    // finish
   // message("Dcoumento Rejeitado", "{$cfg_site}");
  }
  else
    redirect("{$cfg_site}document/manage.php");
}	

?>
