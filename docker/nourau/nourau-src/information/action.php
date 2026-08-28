<?php

// NOU-RAU - Copyright (C) 2002 Instituto Vale do Futuro
// This program is free software; see COPYING for details.
//document action: /document/action.php

require_once '../include/start.php';
require_once BASE . 'include/defs_d.php';
require_once BASE . 'include/util_d.php';

$params = $_REQUEST;
$op = isset($params['op']) && $params['op'] !='' ? $params['op'] : '0'; 

// Controle de acesso proprio deste endpoint: exige sessao autenticada com
// nivel de administrador. Nao depende de check_administrator_rights(), que
// retorna normalmente quando a sessao nao tem nivel definido (anonimo).
$auth_uid   = isset($_SESSION['suid'])   ? $_SESSION['suid']   : '';
$auth_level = isset($_SESSION['slevel']) ? $_SESSION['slevel'] : '';
if ($auth_uid === '' || !is_numeric($auth_level) || (int) $auth_level !== ADM_LEVEL) {
  http_response_code(403);
  header('Content-Type: application/json; charset=utf-8');
  echo json_encode(array('status' => false, 'error' => 'Acesso negado'));
  exit();
}

// Executa SQL com parametros vinculados (pg_query_params), para que valores
// vindos da requisicao nunca sejam concatenados na consulta.
function db_query_params ($sql, $bind)
{
  global $db_conn;

  if (!($q = pg_query_params($db_conn, $sql, $bind)))
    fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");
  return $q;
}


//Inserir o Tipo de Informação
if ($op == 'i') { // ---------------- accept document after verification
  //validate access
 
   check_administrator_rights();
   $resp = array();
   
   $type_name = $_POST['type_name'];
   $status = false;
   $resp['status'] = false;
   $resp['id'] = 0;


   db_query_params('INSERT INTO type_information (name) VALUES ($1)', array($type_name));
   $id = db_simple_query("select max(id) from type_information");

   //echo " $id ";
   $resp['status'] = true;
   $resp['id'] =$id;
   echo json_encode($resp); 
}


//Apaga o Tipo de Informação
if ($op == 'd') { // ---------------- accept document after verification
  //validate access
   check_administrator_rights();
     
  $id = $params['id'];
  
   $resp['status'] = false;
   
   db_query_params('DELETE FROM type_information WHERE id = $1', array($id));

   $resp['status'] = true;
   echo json_encode($resp); 
}

//Atualiza o Tipo de Informação
if ($op == 'u') { // ---------------- accept document after verification
  //validate access
   check_administrator_rights();
      
   $resp['status'] = false;
   
   $type_name = trim($_POST['type_name']);
   $id = $_POST['id'];
 
   db_query_params('UPDATE type_information SET name = $1 WHERE id = $2', array($type_name, $id));

   $resp['status'] = true;
  // $resp['value']="UPDATE FROM type_information SET type_name = '".$type_name."' WHERE id = ".$id;
   echo json_encode($resp); 
}


//Atribuir tipo de informações a Coleção 
if ($op == 'a') { // ---------------- accept document after verification
  //validate access
  check_administrator_rights();
      
  $resp['status'] = false;
   
  $tid = $_POST['tid'];
  $idtif = $_POST['idtif'];
  
  $topicos= carrega_topicos($tid);
  foreach ($topicos as $topico){
      db_query_params('insert INTO topic_type (topic_id, type_id ) VALUES ($1, $2)', array($topico[0], $idtif));
  }
  
  $resp['status'] = true;
  //$resp['topicos'] = $topicos
  echo json_encode($resp); 
}

function carrega_topicos($tid){

  global $db_conn;
  $topico = array();
 
  $topic = db_query_params('SELECT id FROM topic WHERE parent_id = $1 ORDER BY name', array($tid));
  $topico[]=array($tid); 
  while ($q = db_fetch_array($topic)){
      $topico[]=array($q['id']);
      $resulttopic = db_query_params('SELECT id From topic where parent_id = $1 order by name', array($q['id']));
    while ($qtopic = pg_fetch_array($resulttopic)){
          $topico[]=array($qtopic['id']);
          $resulttopic1 = db_query_params('SELECT id From topic where parent_id = $1 order by name', array($qtopic['id']));
        while ($qtopic1 = pg_fetch_array($resulttopic1)){
            $topico[]=array($qtopic1['id']);
            $resulttopic2 = db_query_params('SELECT id  From topic where parent_id = $1 order by name', array($qtopic1['id']));
        while ($qtopic2 = pg_fetch_array($resulttopic2)){
            $topico[]=array($qtopic2['id']);
            $resulttopic3 = db_query_params('SELECT id  From topic where parent_id = $1 order by name', array($qtopic2['id']));
          while ($qtopic3 = pg_fetch_array($resulttopic3)){
            $topico[]=array($qtopic3['id']);
          }
        }
      }
    }
  }
 
  return $topico;
 }


?>