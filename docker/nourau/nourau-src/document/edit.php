<?php

// NOU-RAU - Copyright (C) 2002 Instituto Vale do Futuro
// This program is free software; see COPYING for details.

require_once '../include/start.php';
require_once BASE . 'include/control.php';
require_once BASE . 'include/defs_d.php';
require_once BASE . 'include/format.php';
require_once BASE . 'include/page_d.php';
require_once BASE . 'include/util.php';
require_once BASE . 'include/util_d.php';

if($_SERVER["REQUEST_METHOD"] == "GET") {
$did = $_GET['did'];
	
}
else {
	
$did = $_POST['did'];
$sent = $_POST['sent'];


// os valores abaixo são gravados com pg_query_params(): não podem ser
// pré-escapados, sob pena de gravar as aspas dobradas no banco
$title = trim($_POST['title']);
$title_en = trim($_POST['title_en']);
$author = trim($_POST['author']);
$autor_principal =  trim($_POST['autor_principal']);

$keywords = trim($_POST['keywords']);
$keywords_en = trim($_POST['keywords_en']);
$abstract = trim($_POST['abstract']);
$description = trim($_POST['description']);
$code = trim($_POST['code']);
$info = trim($_POST['info']);

if (isset($_POST['prefix']))
 $prefix = trim($_POST['prefix']);

$filename = isset($_POST['filename'])?trim($_POST['filename']):'';
$remote = $_POST['remote'];
// arquivo local: o nome é um componente de caminho sob archive/incoming,
// não pode carregar diretórios vindos do pedido
if ($remote == 'n')
  $filename = basename($filename);
if (isset($_POST['remoteold']))
	$remoteold = $_POST['remoteold'];
$cid = trim($_POST['cid']);
$curso = trim($_POST['curso']);
$disciplina = trim($_POST['disciplina']);
$professor = trim($_POST['professor']);
$departamento = trim($_POST['departamento']);
$tipoInformacao =isset($_POST['tipoInformacao'])?$_POST['tipoInformacao']:0;
$capa = isset($_POST['capa'])?trim($_POST['capa']):'';
$source =  trim($_POST['source']);
$nota_versao_ori= trim($_POST['nota_versao_ori']);
$descricao_fisica= trim($_POST['descricao_fisica']);
$doi=isset($_POST['doi'])?trim($_POST['doi']):'';
$acesso_eletronico=isset($_POST['acesso_eletronico'])?trim($_POST['acesso_eletronico']):'';
$nlspi=trim($_POST['nlspi']);
$tipoAcesso = (isset($_POST['tipoAcesso'])?$_POST['tipoAcesso']:0);
$edicao =  trim($_POST['edicao']);
$event_description=isset($_POST['event_description'])?trim($_POST['event_description']):'';
$avulso =isset($_POST['avulso'])?'y':'n';
$ods_id = isset($_POST['ods_id'])?$_POST['ods_id']:NUll;
$view_document = isset($_POST['view_document'])?1:0;

}


// validate input
if (!valid_int($did))
    message("{$cfg_site}document/?code=" . rawurlencode($a['code']),"Parâmetro Inválido !", "failure");

// check access rights
// É preciso sessão autenticada antes de qualquer leitura, gravação ou
// recebimento de arquivo. A verificação fica aqui, acima de todos os
// desvios: com $sent preenchido o POST não chega a form()/page_begin().
if (!isset($_SESSION['suid']) || !valid_int($_SESSION['suid']) ||
    !isset($_SESSION['slevel']) || (int) $_SESSION['slevel'] < USR_LEVEL)
  redirect("{$cfg_site}user/login.php?url=" . rawurlencode($_SERVER['REQUEST_URI']));

$a = get_document($did);

// e é preciso direito sobre este documento (coleção lida do registro)
check_edit_rights($a);

  if (empty($sent)) {
    // first time; load from base
    load();
    form();
  }
  else if ($sent == "Cancelar") {
    // abort editing
      redirect("{$cfg_site}document/?code=" . rawurlencode($a['code']));
  }

$trocaarquivo = 0;


/*Capa do documento*/

if (file_exists($_FILES['fileCapa']['tmp_name'])){
	
	$capa_name = strtolower($_FILES['fileCapa']['name']);
	
	$allowd_file_ext = array("jpg", "jpeg", "png", "gif");
	$parts = explode('.',$capa_name);
	$ext = end($parts);
  $tmp_Capa = $_FILES["fileCapa"]["tmp_name"];

  $capa = $did.".".$ext;
	
	if (in_array($ext, $allowd_file_ext)) { 
	
		if (file_exists("/var/www/html/images/capas/{$capa}")) {
			
			//Apaga o fisicamnete arquivo anterior
			 $fDel = "/var/www/html/images/capas/{$capa}";
			 @unlink($fDel);
		}
		
		//nome do capa para gravar na tabela
		$new = "/var/www/html/images/capas/{$capa}";
	    //chmod($tmp_Capa, 0644);
		 move_uploaded_file($tmp_Capa, $new);

   }
   else {
	  form("O arquivo da capa não é uma imagem.");
	}		
}


if (!empty($ods_id)) {
  if (count($ods_id) > 0 ) 
     $ods_ids="{".implode(',',$ods_id)."}";
       
 }else 
	 $ods_ids='{0}';

$status = $a['status'];


if ($remote == 'n') {

//Quando existe a substituição de arquivo
if (file_exists($_FILES['file']['tmp_name'])){
	$file = $_FILES["file"]["tmp_name"];
  $file_type = $_FILES["file"]["type"];
	$file_name = trim($_FILES['file']['name']);
	$file_size = $_FILES["file"]["size"];
  $parts = explode('.',$file_name);
	$file_ext = end($parts);
	list('fid' => $fid, 'cid' => $cid) = find_format($file_type);
	
	if ($fid == 0)
        form("O tipo de arquivo não é aceito nesta coleção.");

    if ($a['status'] == 'i' || $a['status'] == 'w') {
		 //Apaga o fisicamnete arquivo anterior
	 
     $qDel = db_query("SELECT extension,compress FROM nr_format WHERE id=".$a['format_id']);
		 $aDel = db_fetch_array($qDel);
	
   if (IP_Match('143.106.0.0/16',$_SERVER["REMOTE_ADDR"])) {
// set cookie
   setcookie('nr_doc', $code, 0, '/', $cfg_domain, 0, TRUE);
}	 	 
	 $fDel = "$cfg_dir_incoming/{$a['filename']}";
	

     	if ($aDel['compress'] == 'y')
		   	 $fDel .= '.gz';
        	@unlink($fDel);
		
	
		
	   //Grava o novo arquivo no servidor
		$q2 = db_query("SELECT extension,compress FROM nr_format WHERE id=".$fid);
		$a2 = db_fetch_array($q2);
		chmod($file, 0644);
       
	    $filename = random_string(4) . '-' .str_replace(' ', '_', basename($file_name));
		  $new = "$cfg_dir_incoming/$filename";
		
	   copy($file, $new);
	 /*  if ($a2['compress'] == 'y') {
		  // verifica se o arquivo compacta existe para apaga-lo
		   $filecompact = $new. '.gz';
		  //compacta o arquivo
		  exec("gzip -9 $new");
       }*/
	   
	   
	} else {
		  //Apaga o fisicamnete arquivo anterior
		  $qDel = db_query("SELECT extension,compress FROM nr_format WHERE id=".$a['format_id']);
		  $aDel = db_fetch_array($qDel);
		  $fDel = "$cfg_dir_archive/{$a['topic_id']}/$did.{$aDel['extension']}";

		  if ($aDel['compress'] == 'y')
			 $fDel .= '.gz';
			@unlink($fDel);

		// nome do arquivo para gravar na tabela
		$filename = basename($file_name);
		

		//Grava o novo arquivo no servidor
		$q2 = db_query("SELECT extension,compress FROM nr_format WHERE id=".$fid);
		$a2 = db_fetch_array($q2);
		chmod($file, 0644);

		$new = "$cfg_dir_archive/{$a['topic_id']}/$did.{$a2['extension']}";

		copy($file, $new);
		if ($a2['compress'] == 'y') {
		  // verifica se o arquivo compacta existe para apaga-lo
		  //  $filecompact = $new. '.gz';
		  //compacta o arquivo
		  exec("gzip -9 $new");
       }

   }
   // Identifica que ocorreu uma troca de arquivo
 
  	$trocaarquivo = 1;
	// update file size
    $sql_update = 'UPDATE nr_document SET title=$1,title_en=$2,author=$3,autor_principal =$4,keywords=$5,keywords_en=$6,abstract=$7,description=$8,code=$9,info=$10,status=$11,remote =$12, filename=$13, category_id=$14, format_id=$15, size=$16, updated=\'now\', curso= $17, disciplina = $18, professor = $19, departamento=$20, typeInform_id = $21, capa = $22, source=$23, descricao_fisica=$24, doi=$25, acesso_eletronico=$26, nlspi= $27, tacesso =$28, nota_versao_ori = $29, edicao = $30,  event_description = $31, avulso=$32, ods_id=$33, view_document=$34 WHERE id=$35';
    db_command_params($sql_update,
                      array($title, $title_en, $author, $autor_principal,
                            $keywords, $keywords_en, $abstract, $description,
                            $code, $info, $status, $remote, $filename, $cid,
                            $fid, $file_size, $curso, $disciplina, $professor,
                            $departamento, $tipoInformacao, $capa, $source,
                            $descricao_fisica, $doi, $acesso_eletronico,
                            $nlspi, $tipoAcesso, $nota_versao_ori, $edicao,
                            $event_description, $avulso, $ods_ids,
                            $view_document, $did));
    add_log('n', 'du', "did=$did Troca de arquivo");
}
}else {
	$file_name = $acesso_eletronico;
	$cid = 0;
	$fid = 0;
	$file_size = 0;
	
}



$msg = "Documento salvo";
if ($sent == "Continuar Depois") {
	
    $status = $a['status'];
	$tipoInformacao = !empty($tipoInformacao)?$tipoInformacao:0;
	$msg = 'Documento salvo';
	
}else {
	if ($status == 'i') {
		$status = 'w';
		$topic = get_topic($a['topic_id'], 'name');
		//enviar email 
		$uid = $_SESSION['suid'];
		$corpo_email = "Olá!, <br><br>";
		$corpo_email .= "Recebemos nova solicitação de arquivamento (depósito) de documento junto a Biblioteca Digital da Unicamp.<br><br>";
		$corpo_email  .= "Título: {$title} <br>";
		$corpo_email  .= "Coleção: {$topic} <br><br>";
	  $corpo_email  .= "Acesso rápido: {$cfg_site}document/?code={$code},<br><br>";
		$corpo_email  .= "Este e-mail foi enviado automaticamente pelo sistema SBU/BDU<br><br>";
		
		$email = get_user($uid, 'email');
		send_mail($email,"Documento para aprovação", $corpo_email);
		$msg = 'Documento recebido.';
	}	
}	
	
	
$sql_update = 'UPDATE nr_document SET title=$1,title_en=$2,author=$3,autor_principal =$4,keywords=$5,keywords_en=$6,abstract=$7,description=$8,code=$9,info=$10,status=$11,remote =$12, filename=$13,updated=\'now\', curso= $14, disciplina = $15, professor = $16, departamento=$17, typeInform_id = $18, capa = $19, source=$20, descricao_fisica=$21, doi=$22, acesso_eletronico=$23, nlspi= $24, tacesso =$25, nota_versao_ori = $26, edicao = $27,  event_description = $28, avulso=$29, ods_id=$30, view_document=$31 WHERE id=$32';
db_command_params($sql_update,
                  array($title, $title_en, $author, $autor_principal,
                        $keywords, $keywords_en, $abstract, $description,
                        $code, $info, $status, $remote, $filename, $curso,
                        $disciplina, $professor, $departamento,
                        $tipoInformacao, $capa, $source, $descricao_fisica,
                        $doi, $acesso_eletronico, $nlspi, $tipoAcesso,
                        $nota_versao_ori, $edicao, $event_description,
                        $avulso, $ods_ids, $view_document, $did));

// finish
if ($a['status'] == 'i') {
  
  message("{$cfg_site}",$msg, "success");
}
else {
  add_log('n', 'du', "did=$did");
  message("{$cfg_site}document/?code=" . rawurlencode($code),$msg, "success");
}



/*-------------- functions --------------*/

function form ($msg = "")
{
  global $cfg_max_document_keywords, $cfg_max_document_description,
    $cfg_max_document_info, $cfg_max_document_abstract,
    $cfg_site, $cfg_dir_image, $cfg_dir_image_capas ;
  global  $a, $did, $title, $title_en, $author, $autor_principal, $keywords,
    $keywords_en, $abstract, $description, $code, $info, $filename, $remote, $cid, $curso, $disciplina,
  	$professor, $departamento, $tipoInformacao, $capa, $tid, $source, $descricao_fisica, $doi, $acesso_eletronico, $nlspi, $prefix, $nota_versao_ori, 
    $tipoAcesso, $edicao, $event_description, $avulso, $ods_id, $view_document;

 page_begin();
 
  $topic = get_topic($a['topic_id'], 'name');
  $tid = $a['topic_id'];
  
  if ($a['status'] == 'i') {
    echo html_h("Arquivar documento em: <b> {$topic} </b> ");
    format_warning($msg);
	  echo "<div class=\"text\">\n";
	if ($a['topic_id'] == 'n') {
	    $format = '<b>' . get_format($a['format_id'], 'name') . '</b>';    
         echo  "<p>Documento aceito com formato {$format} <br>\n";
	}
	
  	echo  "Por favor, preencha abaixo todas as informações relacionadas ao arquivo enviado.</p>";
    echo "</div>\n";

  }
  else {
    echo html_h("Editar documento de ". html_b ($topic));
    format_warning($msg);
  }

  if (empty($code))
    $code = $did;
  if (empty($filename))
    $filename = $a['filename'];
  if (empty($remote))
  	$remote = $a['remote'];
if (empty($capa))
    $capa = $a['capa'];
 

  html_form_begin($_SERVER['PHP_SELF'], true, 'multipart/form-data');
  html_form_hidden('did', $did);
  html_form_hidden('cid', $cid);
  html_form_hidden('remoteold', $remote);
  html_form_hidden('remote', $remote);
  html_form_hidden('code', $code);
  html_form_hidden('info', $info);
  html_form_hidden('prefix', $prefix);
  echo "<input type='hidden' id='adid' name='adid' value='". $did."' />";
  
  
    $qtpinf = db_query("SELECT id, name FROM type_information Inner join topic_type on type_information.id =topic_type.type_id  where topic_id ={$tid} order by name");   
	$opt = array();
    $opt[''] = 'Escolha um Tipo de informação';
    while ($b = db_fetch_array($qtpinf)) {
      $tmp = $b['name'];
      $opt[$b['id']] = $tmp;
    }
    html_form_select('Tipo de informação ', 'tipoInformacao', $opt, $tipoInformacao, true);
	

  	 echo "<p>";
     echo "<input type=\"checkbox\" id=\"avulso\" name=\"avulso\" value=\on\" ". ($avulso=="y"?"checked='checked'":"")." \" >  <b>Documento Avulso.</b>";
     echo "</p><br>";
	 
	 echo html_b("Objetivos de Desenvolvimento Sustentável:") . "<br>\n";
  
      
	 $ods_ids = explode(',', trim((string) $ods_id,'{}'));

      echo "<ul class=\"checkbox_ods\">";
        $sqlODS = "SELECT id, description FROM nr_ods ORDER BY ordem";
        $qODS = db_query($sqlODS);

        $ods_list = array();

        while ($r = db_fetch_array($qODS)){
          $ods_list[$r['id']] = $r['description'];         
        }

      foreach ($ods_list as $key => $value) {

          if (in_array($key, $ods_ids)) 
            $checked = 'Checked';            
          else 
            $checked = '';
            
          echo "<li><input type=\"checkbox\"  name=\"ods_id[]\" value=\"$key\" {$checked} > {$value}</li>\n";	
        }
          echo "</ul>";
      echo "<br>";
	 
	 
	 



    html_form_text("Autor Principal", "autor_principal", 80, $autor_principal, 800, false, "Exemplo: Amado, Jorge","Preencher o Autor com sobrenome, nome");

    html_form_text("Título Principal", "title", 80, $title, 250, true, "Exemplo: A morte e a morte de Quincas Berro D'água : romance de Jorge Amado", "Apenas a primeira letra do título, nomes próprios e siglas são em maiúsculo");

    html_form_text ("Título Variante", "title_en", 80, $title_en, 250, false,"", "Apenas a primeira letra do título, nomes próprios e siglas são em maiúsculo");
   
    html_form_area("Autoridade Intelectual",  "author", 10, $author, 3000, false, "Exemplo:&#013; 1 - Peter Atkins, Júlio de Paula&#013;2 - Jorge Amado ; capa e ilustrações de Santa Rosa ", "Preencher o autor forma direta e instituição por extenso");
				 
   
     html_form_area("Palavras-chave[PT]", "keywords", 2, $keywords, $cfg_max_document_keywords, True, "", "Apenas a primeira letra da Palavras-chave, nomes próprios e siglas são em maiúsculo e separados por ponto e vírgula");

  html_form_area("Palavras-chave[EN]","keywords_en", 2, $keywords_en, $cfg_max_document_keywords, false, "", "Apenas a primeira letra da Palavras-chave, nomes próprios e siglas são em maiúsculo e separados por ponto e vírgula");

  
  html_form_area("Resumo", "abstract", 10, $abstract, $cfg_max_document_abstract, false, "","Apenas a primeira letra do resumo, nomes próprios e siglas são em maiúsculo");
 
  html_form_area("Notas", 'description', 6, $description,$cfg_max_document_description, false, "Exemplo: Disponível em: World Wide Web", "Apenas a primeira letra da Notas, nomes próprios e siglas são em maiúsculo");
 
  html_form_area("Apresentações do Evento", "event_description", 6, $event_description, $cfg_max_document_description, false, "Exemplo:&#013; 04/03/2023 - Abertura - https://www.youtube.com/watch?v=wOAajeawPc1&#013; Tarde - Palestras - https://www.youtube.com/watch?v=wOAajeawPc2 &#013; 05/03/2023 - Encerramento - https://www.youtube.com/watch?v=wOAajeawPc3","Preencher com a data ou período do evento e a URL dos vídeos");
  
  
  html_form_text("Imprenta", "source", 20, $source, 100, True, "Exemplo: São Paulo,SP: Livro falante, 2006","Preencher com lugar de publicação editora e ano");
  
   html_form_text("Edição", "edicao", 20, $edicao, 100, false, "Exemplo: 2. ed ou 2nd. ed.  ","Preencher com a informação de edição respeitando o idioma");
   html_form_text("Nota de Versão Original", "nota_versao_ori", 20, $nota_versao_ori, 900, false, "Exemplo: Reprodução de :2. ed., São Paulo, SP : Ediouro, 2002., 212 p., ISBN: 8500011610","Preencher com Nota de versão");
  
  html_form_area("Descrição Física", "descricao_fisica", 6, $descricao_fisica, $cfg_max_document_info, true, "Exemplos:&#013 135 p. :il.&#013 32 p. : PDF ","Preencher com páginas, outros detalhes físicos.");

  html_form_text("Identificador do Objeto Digital", "doi", 20, $doi, 100, false, "Exemplo: https://doi.org/10.1109/5.771073", "Preencher com o DOI ou Handle");
  
  if ($remote == 'n') 
	 $required=false;
  else 
	 $required=true ; 

  html_form_text("Acesso Eletrônico", "acesso_eletronico", 20, $acesso_eletronico, 800, $required, "Exemplo: https://ieeexplore.ieee.org/document/771073", "Preencher com a URL do documento");
  
  
  html_form_area("Número de livro ou série padrão intenacional", "nlspi", 4, $nlspi, $cfg_max_document_info, false, "Exemplos: &#013 ISBN: 9788578500351&#013 ISSN: 0018-9219 &#013 e-ISSN: 1558-2256: PDF ","Preencher com páginas, outros detalhes físicos.");
  

  html_form_text("Curso", "curso", 80, $curso, 100, false, "", "Preencher sem abreviações");
  
  html_form_text("Disciplina", "disciplina", 80, $disciplina, 100, false, "", "Preencher sem abreviações");

  html_form_text("Professor", "professor", 80, $professor, 100, false, "", "Preencher sem abreviações");  
  
  html_form_text("Departamento", "departamento", 80, $departamento, 100, false, "", "Preencher sem abreviações");   
  
  echo "<p>\n";

	  if (!empty($capa)) {
		if (file_exists( $cfg_dir_image_capas."/".$capa)) {
		   echo "<img src=\"$cfg_dir_image/$capa\" width=\"10%\" height=\"10%\"><br><br>\n";
	    }
     }
 	 
     if ($status = 'i') {
		 
		  $label_capa = 'Inserir uma Capa';
		        
		  If (empty($capa)) 
			  $required = TRUE;
		  else 
			 $required = FALSE;  
		   
	 }	 
	 else
	 {		 
		 $label_capa = 'Trocar a Capa'; 
		 $required = FALSE;
	 }	 
 	 
	  html_form_file($label_capa, 'fileCapa',TRUE,'',$required );
	  html_form_hidden('capa', $capa);
   
       	echo "<div id=\"remoten\">";
  	 	if ($remote == 'n' ) {
			
  			echo "<p><label for=\"nomearq\">Trocar o documento principal:</label>\n";
  			echo " <input type=\"file\" id=\"file\" name=\"file\" onchange=\"nome_arquivo(this.value);\"></p>\n";
			
		    echo "<p><label for=\"nomearq\">Nome do arquivo: </label>";
  			echo "<input type=text id=\"nomearq\" name=\"filename\" value='".$filename."' size ='80' Readonly >";
  			echo "</p>\n";
			
			echo "<p>";
			
			$checked = ($view_document == 1)? 'checked':'';
			echo "<input type=\"checkbox\" id=\"view_document\" name=\"view_document\" value=\"$view_document\"  {$checked}  > Visualizar o conteúdo do arquivo PDF.";
			echo "</p><br>";
			
			

 //Carrega os Anexos

 $sqlsf = 'SELECT supplementary_files.id, supplementary_files.filename, supplementary_files.remote FROM supplementary_files INNER JOIN nr_document on supplementary_files.document_id = nr_document.id WHERE supplementary_files.document_id =$1';
 $qsf = db_query_params_d($sqlsf, array($did));
 
 echo "<p><label for=\"nomearq\">Anexos: </label>";
 echo html_button(format_action("Acrescentar Arquivos", "javascript:janelaArquivoSuplementar('arquivosuplementar.php?did=".$did."&tid=".$a['topic_id']."&op=i&status=".$a['status']."',370,540)"));

 echo "<div class= 'arquivo_suplementar' id = 'arquivo_suplementar' >";
 
 echo "<table class ='arqsupl'>";

 if (db_rows($qsf)==0) {
	 echo "<tr><td><b>Nennhum arquivo encontado</b></td></tr>";
 } else {
	 
	$i = 1;

    	while ($rowsf = db_fetch_array($qsf)){
			echo "<tr>";
			echo "<td>$i. ".$rowsf['filename']."</a></td>";
			echo "<td><a href =\"javascript:janelaArquivoSuplementar('arquivosuplementar.php?did=".$did."&id=".$rowsf['id']."&tid=".$a['topic_id']."&op=d&status=".$a['status']."',530,450)\">"._('Remove')."</a></td>";
			echo "</tr>";
			$i += 1;
     }
  }
echo "</table>";
echo "</div>";

  $default = (!empty($tipoAcesso)?$tipoAcesso :0);

 $optuser = array (0=>"<b>Acesso Aberto</b>: qualquer pessoa pode acessar o documento sem nenhum tipo de restrição.", 1=>"<b>Acesso Unicamp</b>: apenas à comunidade da Unicamp pode acessar o documento sem nenhum tipo de restrição. " , 2=>"<b>Acesso Restrito</b>: o documento fica com restrições de acesso, somente pessoas autorizadas poderão acessá-lo.");
 
 html_form_radio('Permissão de acesso ao material', 'tipoAcesso', $optuser, $default); 


}


?>
<script type="text/javascript">
 var msg = sessionStorage.getItem("my_report");
 var type = sessionStorage.getItem("type");
 
 let UrlSite = siteUrl;

   if( msg ){
	   mostraDialogo(msg, type, 4500); 	
       sessionStorage.removeItem("my_report");
	   sessionStorage.removeItem("type");
  }
	
	$(document).ready(function() {
	  
	   $("#descartar")
			.button()
			.click(function() {
				$("#dialog-descartar").dialog("open");
				return false;
	  });	
			
		
	 
	 $( "#dialog-descartar" ).dialog({
      autoOpen: false, 
		  resizable: false,
		  height: "auto",
		  width: 400,
		  modal: true,
		  buttons: {
			"Sim": function() {
				  $( this ).dialog( "close" );
				   var did =  $("#adid").val();
				   var op = 'dc'; 
				   var conf = 'Sim'
				    console.log(op  +' ' + did + ' ' +conf);
				   
				   $.post("action.php",{op:op,did:did,conf:conf},
				  function(resposta){
						if (resposta == 'sucesso') {    					 
						    var url =  UrlSite ;
						    sessionStorage.setItem("my_report", <?php echo json_encode( "<strong>O Documento foi descartado!</strong>" ); ?> );
						    sessionStorage.setItem("type", <?php echo json_encode("success"); ?> );
						    location.replace(url);
						}
						else if (resposta == 'error') {
							 var msg = "<strong>Arquivo não encontrado!<strong>";    
							 mostraDialogo(msg, 'failure', 4500); 	 
						} 
				        else {
							var msg = "<strong>Acesso Negado!<strong>";    
							 mostraDialogo(msg, 'failure', 4500);
						}
				 });	         
		  	},
			Cancelar: function() {
			  $( this ).dialog( "close" );
			}
		  }
     });
	     


    function redirect_page(){
	  //window.location = location.href;
	  window.location.reload();
	}
	
 });	
	

</script> 


<?php

if ($a['status'] == 'i') {
   echo "<div class=\"text\">\n"; 
    echo "<p>Observe que o arquivamento do seu documento depende da aprovação do responsável por este tópico.</p>\n";
    echo "</div>";

    /*Descartar */
	echo "<div class=\"botao\">";
    echo "<button class='button_action' id='descartar'><span >Descartar esse Documento</span></button>"; 
    echo "<div id=\"dialog-descartar\" title=\"Decartar esse Documento ?\">";
    echo "<p><span class=\"ui-icon ui-icon-alert\" style=\"float:left; margin:12px 12px 20px 0;\"></span>Você deseja descartar o documento:\"{$a['title']}\" ?</p>";
    echo "</div>";
		echo "</div>";
   
	echo "<div class=\"botao\">";
		html_form_submit('Salvar', 'sent');
	echo "</div>";
	echo "<div class=\"botao\">";
		html_form_submit('Continuar Depois', 'sent', false);
		echo "</div>";
  }
  else {
     echo "<div class=\"botao\">";
		html_form_submit('Salvar', 'sent');
		echo "</div>";
		echo "<div class=\"botao\">";
		html_form_submit('Cancelar', 'sent', false);
		echo "</div>";
  }
  
  
 
  html_form_end();
  

 echo "</div> <!-- end #mainContent1 -->\n " ;
  if ($a['status'] == 'i')
    page_end();
  else  {	  
    page_end();
  
  }
  exit();
}

function load ()
{
  global $a, $title, $title_en, $author, $autor_principal, $keywords, $keywords_en, $abstract,
    $description, $code, $info, $filename, $remote, $cid, $curso, $disciplina, $departamento, $tipoInformacao, $professor, $capa, $tid, $source, 
    $descricao_fisica, $doi, $acesso_eletronico, $nlspi, $prefix, $nota_versao_ori, $tipoAcesso, $edicao, $event_description, $avulso, $ods_id, $view_document;

  $title = $a['title'];
  $title_en = $a['title_en'];
  $author = $a['author'];
  $autor_principal = $a['autor_principal'];
  $keywords = $a['keywords'];
  $keywords_en = $a['keywords_en'];
  $abstract = $a['abstract'];
  $description = $a['description'];
  $code = $a['code'];
  $info = $a['info'];
  $filename = $a['filename'];
  $remote = $a['remote'];
  $cid = $a['category_id'];
  $curso = $a['curso'];
  $disciplina = $a['disciplina'];
  $professor = $a['professor'];
  $departamento =  $a['departamento'];
  $tipoInformacao = $a['typeinform_id'];
  $capa= $a['capa'];
  $tid = $a['topic_id'];
  $source=$a['source'];
  $nota_versao_ori = $a['nota_versao_ori'];
  $descricao_fisica=$a['descricao_fisica'];
  $doi =$a['doi'];
  $acesso_eletronico=$a['acesso_eletronico']; 
  $nlspi=$a['nlspi'];
  $tipoAcesso = $a['tacesso'];
  $edicao = $a['edicao'];
  $event_description = $a['event_description'];
  $avulso = $a['avulso'];
  $ods_id = $a['ods_id'];
  $view_document=$a['view_document'] ;
  
  if ($a['status'] == 'i' || $a['status'] == 'w') {
    $prefix = substr($a['filename'], 0, 4);
  } 
  else 
	$prefix = '';
  
  
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

/* Consulta com valores ligados. include/db.php só aceita SQL pronto, por
   isso as duas funções abaixo falam direto com a conexão, como ele faz. A
   mensagem de erro é a genérica: a consulta não volta para o navegador. */

function db_query_params_d ($sql, $params)
{
  global $db_conn;

  if (!($q = pg_query_params($db_conn, $sql, $params)))
    fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");
  return $q;
}

function db_command_params ($sql, $params)
{
  return @pg_affected_rows(db_query_params_d($sql, $params));
}

/* Direito de edição sobre um documento. Apurado aqui, sem depender dos
   auxiliares de include/control.php e include/util_d.php, para que este
   arquivo se defenda sozinho:

     - administrador edita qualquer documento;
     - curador (mantenedor/responsável) edita os documentos das coleções
       em que está inscrito, como em document/action.php (via
       check_maintainer_rights) e em document/index.php;
     - depositante edita o documento que depositou — ou o de uma coleção
       sua — enquanto está em curadoria, como em document/index.php
       ('i' ou 'w') e em collab_index.ini.

   A coleção vem sempre do registro do documento, nunca do pedido. */

function check_edit_rights ($a)
{
  global $cfg_site;

  $uid = (string) $_SESSION['suid'];
  $level = (int) $_SESSION['slevel'];
  $tid = isset($a['topic_id']) ? (string) $a['topic_id'] : '';
  $owner = isset($a['owner_id']) ? (string) $a['owner_id'] : '';

  if ($level == ADM_LEVEL)
    return;

  if ($level == MNT_LEVEL || $level == RES_LEVEL) {
    if (is_topic_user($tid, $uid))
      return;
  }
  else if ($level == USR_LEVEL && ($a['status'] == 'i' || $a['status'] == 'w')) {
    if ($owner === $uid || is_topic_user($tid, $uid))
      return;
  }

  message("{$cfg_site}document/?code=" . rawurlencode($a['code']),"Acesso Negado !", "failure");
}

function is_topic_user ($tid, $uid)
{
  if (!valid_int($tid) || !valid_int($uid))
    return false;
  $q = db_query_params_d('SELECT 1 FROM topic_users WHERE topic_id=$1 AND users_id=$2',
                         array($tid, $uid));
  return (db_rows($q) > 0);
}



?>
