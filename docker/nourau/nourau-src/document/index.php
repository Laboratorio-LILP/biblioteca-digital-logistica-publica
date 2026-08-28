<?php

// NOU-RAU - Copyright (C) 2002 Instituto Vale do Futuro
// This program is free software; see COPYING for details.

require_once '../include/start.php';
require_once BASE . 'include/defs_d.php';
require_once BASE . 'include/format.php';
require_once BASE . 'include/format_d.php';
require_once BASE . 'include/format_t.php';
require_once BASE . 'include/page.php';
require_once BASE . 'include/page_d.php';
require_once BASE . 'include/util.php';
require_once BASE . 'include/util_d.php';

if (isset ($_GET['code']))
   $code = $_GET['code'];

if (isset ($_GET['down']))
	$down = $code = $_GET['down'];	

if (isset ($_GET['view']))
	$view = $code = $_GET['view'];

$idsf = isset ($_GET['idsf'])?$_GET['idsf']:null;


// send a cookie to certificate that the user has opened the page
//  before downloading the document, only if it is not a Google robot
/*if (IP_Match('143.106.0.0/16',$_SERVER["REMOTE_ADDR"])) {
// set cookie
   setcookie('nr_doc', $code, 0, '/', $cfg_domain, 0, TRUE);
}	 	 */


// download document
if (!empty($down)) {
        view_document($down, true, $idsf, false);
} 


page_begin(); 

// translate from document id to code and redirect
if (!empty($did)) {
  if (!valid_int($did))
      message($cfg_site,"Parâmetro inválido", "failure");
     $code = get_document($did, 'code');

}
// if empty go to search page
if (empty($code))
  redirect("{$cfg_site}");



// get document
$q = doc_query_params('SELECT * FROM nr_document WHERE code=$1', array($code));
if (!db_rows($q))
    message($cfg_site,"Documento não encontrado", "failure");
$a = db_fetch_array($q);
$did = $a['id'];

if ($a['status'] == 'd')
 message($cfg_site,"Documento não encontrado", "failure");
 
  

?>
<script type="text/javascript">

 	var msg = sessionStorage.getItem("my_report");
  	var type = sessionStorage.getItem("type");


    let UrlSite = siteUrl;

 	console.log(UrlSite);
	

   if( msg ){
	   mostraDialogo(msg, type, 4500); 	
       sessionStorage.removeItem("my_report");
	   sessionStorage.removeItem("type");
	}
	
	$(document).ready(function() {

	 var label1 = 'Sim';
     var label2 = 'Não';

	var theButtons = {};
    theButtons[label1] = function() { troca_base();};
	theButtons[label2] = function() { $( this ).dialog("close");};

   $('#remove a').each(function() {
			var $link = $(this);
			var $dialog = $('<div></div>')
				.load($link.attr('href'))

				.dialog({
					autoOpen: false,
					modal:true,
					title: $link.attr('title'),
					width: 620
				});

			$link.click(function() {
				$dialog.dialog('open');
				return false;
			});
		});
	

    $("#editar")
			.button()
			.click(function() {
				var did = $(this).attr("data-id")
				var url = UrlSite+"document/edit.php?did="+did;
				location.replace(url);
				return false;
	   });
 
		
	 $("#trocabase")
			.button()
			.click(function() {
				$("#dialog_trocabase").dialog("open");
				return false;
	   });
 
	  
	  $("#remover")
			.button()
			.click(function() {
				$("#dialog-remover").dialog("open");
				return false;
	  });
		
	  $("#aprovar")
			.button()
			.click(function() {
				$("#dialog-aprovar").dialog("open");
				return false;
	  });	
	  
	   $("#rejeitar")
			.button()
			.click(function() {
				$("#dialog-rejeitar").dialog("open");
				return false;
	  });	
			
		

	 $("#dialog_trocabase").dialog({
			autoOpen: false,
			modal:true,
	  		resizable: false,
			width: 620,
			height: "auto",
			buttons:{
				 "Sim":function() { 
				     troca_base();
			         },
				 "Não": function() {
					$("select[name=tid]").val("0");
					$('.validateTips').html("");
				    $( this ).dialog( "close" );
			  }
			}		  
	  });
	  
	  $( "#dialog-remover" ).dialog({
	     
          autoOpen: false, 
		  resizable: false,
		  height: "auto",
		  width: 400,
		  modal: true,
		  buttons: {
			"Apagar": function() {
				  $( this ).dialog( "close" );
				   var did =  $("#rdid").val();
				   var tid = $("#rtid").val();
				   var op = 'd'; 
				   var conf = 'Sim'
				   $.post("action.php",{op:op,did:did,conf:conf},
				  function(resposta){
						if (resposta == 'sucesso') {    					 
						    var url = UrlSite+"document/list.php?tid="+tid;
						    sessionStorage.setItem("my_report", <?php echo json_encode( "<strong>O Documento foi Apagado!</strong>" ); ?> );
						    sessionStorage.setItem("type", <?php echo json_encode("success"); ?> );
						    location.replace(url);
						}
				 });	         
		  	},
			Cancelar: function() {
			  $( this ).dialog( "close" );
			}
		  }
     });
	 
	 
	 $( "#dialog-aprovar" ).dialog({
          autoOpen: false, 
		  resizable: false,
		  height: "auto",
		  width: 400,
		  modal: true,
		  buttons: {
			"Sim": function() {
				  $( this ).dialog( "close" );
				   var did =  $("#adid").val();
				   var op = 'a';
				   var conf = 'Sim';
                    console.log(op, did, conf);
				   $.post("action.php",{op:op,did:did,conf:conf},
				  function(resposta){
						if (resposta == 'sucesso') {    
                                                    console.log(resposta)					 
						    var url = UrlSite+"document/manage.php";
						    sessionStorage.setItem("my_report", <?php echo json_encode( "<strong>O Documento foi aprovado!</strong>" ); ?> );
						    sessionStorage.setItem("type", <?php echo json_encode("success"); ?> );
						    location.replace(url);
						}
						else if (resposta == 'error') {
							 var msg = "<strong>Arquivo não encontrado!<strong>";    
							 mostraDialogo(msg, 'failure', 4500); 	 
                                                          console.log(resposta)
						}else if (resposta == 'error_arquivo') {
                                                          console.log(resposta)
					        	var msg = "<strong>Item sem arquivo principal!<strong>";
                                                         mostraDialogo(msg, 'failure', 4500);
						} else {
							var msg = "<strong>Acesso Negado!<strong>";    
							 mostraDialogo(msg, 'failure', 4500);
							console.log(resposta);
						}
				 });	         
		  	},
			Cancelar: function() {
			  $( this ).dialog( "close" );
			}
		  }
     });
	 
	 
	 $( "#dialog-rejeitar" ).dialog({
          autoOpen: false, 
		  resizable: false,
		  height: "auto",
		  width: 400,
		  modal: true,
		  buttons: {
			"Sim": function() {
				  $( this ).dialog( "close" );
				   var did =  $("#adid").val();
				   var op = 'r'; 
				   var conf = 'Sim'
				   $.post("action.php",{op:op,did:did,conf:conf},
				  function(resposta){
						if (resposta == 'sucesso') {    					 
						    var url = UrlSite+"document/manage.php";
						    sessionStorage.setItem("my_report", <?php echo json_encode( "<strong>O Documento foi rejeitado!</strong>" ); ?> );
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
	 
	 
	  function troca_base(){
		
        var  mensagem = '';   
		var tid = $("select[name=tid]").val();
		var tidold = $("#tidold").val();
		var did = $("#did").val();
		var op = $("#op").val();
		

		if (tid =='0') {
          $('.validateTips').html('Escolha uma base');
          return false;
        } else {
		  $('.validateTips').html('');
		}
 
       
	    $.post("action.php",{op:op,did:did,tid:tid,tidold:tidold},
		function(resposta){
			if (resposta == 'sucesso') {
			  setTimeout("redirect_page()",1000); 
			  $("#dialog_trocabase").dialog("close");
			  //alert('O documento foi trocado'); 
              sessionStorage.setItem("my_report", <?php echo json_encode( "<strong>O Documento foi trocado de Coleção!</strong>" ); ?> );
			  sessionStorage.setItem("type", <?php echo json_encode("success"); ?> );			 
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
      } 
	  
	});

    function redirect_page(){
	  //window.location = location.href;
	  window.location.reload();
	}
	
	
	

</script> 


<?php

// get display mode
$topic = htmlspecialchars(get_topic($a['topic_id'], 'name'));
if ($a['status'] == 'v') {
	 breadcrumb(array($cfg_site=>'Início', 'document/manage.php'=>'Curadoria'));
   //echo "<p class='breadcrumb'><a href='{$cfg_site}'>In&iacute;cio</a><span>&gt;&gt;</span><a href='{$cfg_site}document/manage.php'>Gerenciar</a></p>";
  check_administrator_maintainer_rights();
  // check_user_rights();
  $msg = _('Verify:') . ' ' . $topic;
  $filename = substr($a['filename'], 5); // remove random prefix
}
else if ($a['status'] == 'w') {
  
 
 //check_user_rights();
 //check_administrator_maintainer_rights();
 
 if (is_collab()) {
	 breadcrumb(array($cfg_site=>'Início'));
      $msg = "Editar" . ' ' . $topic;
   $filename = substr($a['filename'], 5); // remove random prefix
 }else { 	 
    breadcrumb(array($cfg_site=>'Início', 'document/manage.php'=>'Curadoria'));
   $msg = "Aprovar" . ' ' . $topic;
   $filename = substr($a['filename'], 5); // remove random prefix
 } 
}
else if ($a['status'] == 'a') {
   $msg = "";
  $filename = $a['filename'];
}
else
 message($cfg_site,"Acesso Negado", "failure");

if (empty($opt))
 	$opt=1;

// show topic path
if ($a['status'] == 'a')
  format_path($a['topic_id'], "{$cfg_site}document/list.php", true, $origem[$opt], $origemlink[$opt]);

echo "<div class =\"info-boxes\">";
echo html_h($msg);

echo "<p>\n";

format_document($a['title'], $a['title_en'],$a['author'], $a['autor_principal'],
                $a['keywords'], $a['keywords_en'],
                $a['description'], $a['abstract'],
                $code, $a['info'], $a['created'],
                $a['updated'], $a['owner_id'], $a['category_id'],
                $filename, $a['size'], $a['format_id'],$a['visits'], $a['downloads'], $a['remote'], $did, $a['topic_id'], 
				$a['curso'], $a['disciplina'], $a['professor'], $a['departamento'], $a['typeinform_id'], $a['capa'], 
				$a['source'], $a['descricao_fisica'],$a['doi'], $a['acesso_eletronico'],$a['nlspi'], 
				$a['nota_versao_ori'], $a['tacesso'], $a['edicao'],$a['event_description'],$a['avulso'], $a['ods_id']  );

 // view/download actions
 $code = rawurlencode($code);
 

 if (is_collab()) {
  
   //O depositante pode editar apenas os documentos que ele inserir que estão em aprovação
  if ( $a['status'] == 'i' || $a['status'] == 'w')
     echo "<button class='button_action' id='editar' data-id='".$did."'><span style='text-decoration:underline'>Editar esse Documento</span></button> ";	
 }
 elseif (is_maintainer() ) {
	 
   //O Curador pode editar os documentos Inseridos e que estão em aprovação. Aprovar e reprovar um documento
	if (check_topic_users_edit($a['topic_id'], $_SESSION['suid']) == TRUE) {
		echo "<button class='button_action' id='editar' data-id='".$did."'><span style='text-decoration:underline'>Editar esse Documento</span></button> ";			
	   
		if  ($a['status'] == 'w') {
			echo "<button class='button_action' id='aprovar'><span style='text-decoration:underline'>Aprovar esse Documento</span></button> ";
			echo "<div id=\"dialog-aprovar\" title=\"Aprovar Documento ?\">";
			echo "<input type='hidden' id='adid' name='did' value='". $did."' />";
			echo "<p><span class=\"ui-icon ui-icon-alert\" style=\"float:left; margin:12px 12px 20px 0;\"></span>Você deseja aprovar o documento?</p>";
			echo "</div>";
						  
			echo "<button class='button_action' id='rejeitar'><span style='text-decoration:underline'>Rejeitar esse Documento</span></button>";
			echo "<div id=\"dialog-rejeitar\" title=\"Rejeitar Documento ?\">";
			echo "<input type='hidden' id='adid' name='did' value='". $did."' />";
			echo "<p><span class=\"ui-icon ui-icon-alert\" style=\"float:left; margin:12px 12px 20px 0;\"></span>Você deseja rejeitar o documento?</p>";
			echo "</div>";
		}	
	}
		
 }	
 elseif ( is_responsable()){
	
	echo "<button class='button_action' id='editar' data-id='".$did."'><span style='text-decoration:underline'>Editar esse Documento</span></button> ";	

	if (  $a['status'] == 'w'){
		echo "<button class='button_action' id='aprovar'><span style='text-decoration:underline'>Aprovar esse Documento</span></button> ";
		echo "<div id=\"dialog-aprovar\" title=\"Aprovar Documento ?\">";
		echo "<input type='hidden' id='adid' name='did' value='". $did."' />";
		echo "<p><span class=\"ui-icon ui-icon-alert\" style=\"float:left; margin:12px 12px 20px 0;\"></span>Você deseja aprovar o documento?</p>";
		echo "</div>";
		
		
		echo "<button class='button_action' id='rejeitar'><span style='text-decoration:underline'>Rejeitar esse Documento</span></button>";
		echo "<div id=\"dialog-rejeitar\" title=\"Rejeitar Documento ?\">";
		echo "<input type='hidden' id='adid' name='did' value='". $did."' />";
		echo "<p><span class=\"ui-icon ui-icon-alert\" style=\"float:left; margin:12px 12px 20px 0;\"></span>Você deseja rejeitar o documento?</p>";
		echo "</div>";
    }	

	if  ($a['status'] == 'a') {
		
		
		echo "<button class='button_action' id='remover'><span style='text-decoration:underline'>Remover esse Documento</span></button>"; 
		echo "<div id=\"dialog-remover\" title=\"Remover esse Documento ?\">";
		echo "<input type='hidden' id='rdid' name='rdid' value='". $did."' />";
		echo "<input type='hidden' id='rtid' name='rtid' value='". $a['topic_id']."' />";
		echo "<p><span class=\"ui-icon ui-icon-alert\" style=\"float:left; margin:12px 12px 20px 0;\"></span>Você deseja remover o documento:\"{$a['title']}\" ?</p>";
		echo "</div>";
		
			echo "<button class='button_action' id='trocabase'><span style='text-decoration:underline'>Trocar de Coleção</span></button>";

		echo "<div id='dialog_trocabase' title= 'Trocar de Coleção'>";
			echo "<p class='validateTips'></p>";
			echo "<div id='formRemember'>";
			    $pid = get_topic($a['topic_id'], 'parent_id');
				echo "<form method='post'>";
				echo "<p><label><b>Coleções:</b></label>";
				echo "<select name='tid' size='1' id='troca_colecao' required >";
				echo "<option selected='selected'  value=''>-- escolha uma destas coleções --</option>";
					//$qt = db_query("SELECT id,name,parent_id FROM topic WHERE parent_id =$pid  ORDER BY name");
					
					$qt = db_query("SELECT id,name,parent_id,archieve FROM topic  where  parent_id = 0   ORDER BY parent_id, name");
					while ($at = db_fetch_array($qt)) {
        					$qsubtid = db_query("SELECT id,name,parent_id,archieve FROM topic WHERE parent_id = {$at['id']}  ORDER BY name");
                            if ($at['archieve']=='n' || $at['id'] == $a['topic_id'] ) {
								echo "<optgroup label = '".$at['name']."'>";
							}  else {
                               if ($at['parent_id'] == 0) 
								       echo "<option class= 'bold' value='".$at['id']."'>{$at['name']}</option>"; 
								else 									
									 echo "<option value='".$at['id']."'>{$at['name']}</option>";   
							} 							
							 while ($asubtid = db_fetch_array($qsubtid)) {
									   
									   $qsubtid1 = db_query("SELECT id,name,parent_id,archieve FROM topic WHERE parent_id = {$asubtid['id']}  ORDER BY name");
									  
									    if ($asubtid['archieve']=='n' || $asubtid['id'] == $a['topic_id']) 
										     echo "<optgroup label = '".$asubtid['name']."'>";
									    else  
											echo "<option value='".$asubtid['id']."'>{$asubtid['name']}</option>";
									  			 
										   
										    while ($asubtid1 = db_fetch_array($qsubtid1)) {

										       $qsubtid2 = db_query("SELECT id,name,parent_id,archieve FROM topic WHERE parent_id = {$asubtid1['id']}  ORDER BY name");
												if ($asubtid1['archieve']=='n' || $asubtid1['id'] == $a['topic_id']) 
													echo "<optgroup label = '".$asubtid1['name']."'>";
												else  
													echo "<option value='".$asubtid1['id']."'>{$asubtid1['name']}</option>";
												
												while ($asubtid2 = db_fetch_array($qsubtid2)) {
														echo "<option value='".$asubtid2['id']."'>{$asubtid2['name']}</option>";										
												}
												
												
												
										   }
												   
							}
							echo "</optgroup>";	  	 
							 echo "</optgroup>";
						    echo "</optgroup>";
					}
				echo "</select>";
				echo "</p>";
				echo "<input type='hidden' id='did' name='did' value='". $did."' />";
				echo "<input type='hidden' id='op' name='op' value='t'/>";
				echo "<input type='hidden' id='tidold' name='tidold' value='". $a['topic_id']."' />";
				echo "</form>";
			echo "</div>";
		echo "</div>";     
		
		
	}	


}
 elseif (is_administrator() ) {
	 
	echo "<button class='button_action' id='editar' data-id='".$did."'><span style='text-decoration:underline'>Editar esse Documento</span></button> ";	 
	
	 if  ($a['status'] == 'w') {
		
	     echo "<button class='button_action' id='aprovar'><span style='text-decoration:underline'>Aprovar esse Documento</span></button> ";
		 echo "<div id=\"dialog-aprovar\" title=\"Aprovar Documento ?\">";
		 echo "<input type='hidden' id='adid' name='did' value='". $did."' />";
		 echo "<p><span class=\"ui-icon ui-icon-alert\" style=\"float:left; margin:12px 12px 20px 0;\"></span>Você deseja aprovar o documento?</p>";
		 echo "</div>";
		 
		 
		 echo "<button class='button_action' id='rejeitar'><span style='text-decoration:underline'>Rejeitar esse Documento</span></button>";
		 echo "<div id=\"dialog-rejeitar\" title=\"Rejeitar Documento ?\">";
		 echo "<input type='hidden' id='adid' name='did' value='". $did."' />";
		 echo "<p><span class=\"ui-icon ui-icon-alert\" style=\"float:left; margin:12px 12px 20px 0;\"></span>Você deseja rejeitar o documento?</p>";
		 echo "</div>";
   }	
	
	
	
	if  ($a['status'] == 'a') {
		
		
	 	 echo "<button class='button_action' id='remover'><span style='text-decoration:underline'>Remover esse Documento</span></button>"; 
         echo "<div id=\"dialog-remover\" title=\"Remover esse Documento ?\">";
         echo "<input type='hidden' id='rdid' name='did' value='". $did."' />";
		 echo "<input type='hidden' id='rtid' name='rtid' value='". $a['topic_id']."' />";
         echo "<p><span class=\"ui-icon ui-icon-alert\" style=\"float:left; margin:12px 12px 20px 0;\"></span>Você deseja remover o documento:\"{$a['title']}\" ?</p>";
         echo "</div>";
		
		 echo "<button class='button_action' id='trocabase'><span style='text-decoration:underline'>Trocar de Coleção</span></button>";

		 echo "<div id='dialog_trocabase' title= 'Trocar de Coleção'>";
			echo "<p class='validateTips'></p>";
			echo "<div id='formRemember'>";
			    $pid = get_topic($a['topic_id'], 'parent_id');
				echo "<form method='post'>";
				echo "<p><label><b>Coleções:</b></label>";
				echo "<select name='tid' size='1' id='troca_colecao' required >";
				echo "<option selected='selected'  value=''>-- escolha uma destas coleções --</option>";
					//$qt = db_query("SELECT id,name,parent_id FROM topic WHERE parent_id =$pid  ORDER BY name");
					
					$qt = db_query("SELECT id,name,parent_id,archieve FROM topic  where  parent_id = 0   ORDER BY parent_id, name");
					while ($at = db_fetch_array($qt)) {
        					$qsubtid = db_query("SELECT id,name,parent_id,archieve FROM topic WHERE parent_id = {$at['id']}  ORDER BY name");
                            if ($at['archieve']=='n' || $at['id'] == $a['topic_id'] ) {
								echo "<optgroup label = '".$at['name']."'>";
							}  else {
                               if ($at['parent_id'] == 0) 
								       echo "<option class= 'bold' value='".$at['id']."'>{$at['name']}</option>"; 
								else 									
									 echo "<option value='".$at['id']."'>{$at['name']}</option>";   
							} 							
							 while ($asubtid = db_fetch_array($qsubtid)) {
									   
									   $qsubtid1 = db_query("SELECT id,name,parent_id,archieve FROM topic WHERE parent_id = {$asubtid['id']}  ORDER BY name");
									  
									    if ($asubtid['archieve']=='n' || $asubtid['id'] == $a['topic_id']) 
										     echo "<optgroup label = '".$asubtid['name']."'>";
									    else  
											echo "<option value='".$asubtid['id']."'>{$asubtid['name']}</option>";
									  			 
										   
										    while ($asubtid1 = db_fetch_array($qsubtid1)) {

										        echo "<option value='".$asubtid1['id']."'>{$asubtid1['name']}</option>";
										   }
										  				   
							 }
							 echo "</optgroup>";
						    echo "</optgroup>";
					}
				echo "</select>";
				echo "</p>";
				echo "<input type='hidden' id='did' name='did' value='". $did."' />";
				echo "<input type='hidden' id='op' name='op' value='t'/>";
				echo "<input type='hidden' id='tidold' name='tidold' value='". $a['topic_id']."' />";
				echo "</form>";
			echo "</div>";
		echo "</div>";     
          
 }
 
 } 
 


// finish
 echo "</div> <!-- end #mainContent1 -->\n " ;
if ($a['status'] == 'a')
  page_end("{$cfg_site}document/list.php?tid={$a['topic_id']}");
else
  page_end("{$cfg_site}document/manage.php");


/*-------------- functions --------------*/

function format_document ($title, $title_en, $author, $autor_principal, 
                          $keywords, $keywords_en, $description,$abstract,
                          $code, $info, $created, $updated, $owner_id,
                          $category_id, $filename, $size, $format_id,
                          $visits, $downloads, $remote, $did, $topic_id, $curso, $disciplina, $professor, $departamento, 
			               $typeinform_id, $capa, $source, $descricao_fisica, $doi, $acesso_eletronico, $nlspi, $nota_versao_ori, $tacesso, $edicao, $event_description, $avulso, $ods_id )
{
  global $cfg_site,$cfg_dir_image,$cfg_dir_image_capas, $cfg_site_wp;


echo "<div class='row'>";
	echo "<div class='column left'>";

		  if (!empty($capa)) {
				if (file_exists($cfg_dir_image_capas."/".$capa)) {
				   echo "<img src=\"{$cfg_dir_image}/$capa\" width=\"15%\" height=\"15%\"><br><br>\n";
			  }
		  }
 echo "</div>";
 
 echo "<div class='column right'>";
 if ($cfg_site_wp <> '')
  echo "<div class='info well'>Use este identificador para citar ou linkar para este item: <code><a href=$cfg_site_wp=$code target='_blank'>$cfg_site_wp=$code</a></code></div>";
  
  if ($typeinform_id <> 0 ) {
    $q = db_query("SELECT name FROM type_information WHERE id= $typeinform_id ");
    $ti = db_fetch_array($q);
    format_line('Tipo de Informação', $ti['name']);
 } 
 else 
    format_line('Tipo de Informação','Não especificada');

    
  if (find_parent($topic_id) == 2 ) {
    $doc_avulso = ($avulso == 'y')?'Sim':'Não';
    format_line("Documento avulso",  $doc_avulso);
	
	 /* Exibe os ODS */

	 
	if (!is_null($ods_id) ){ 

		$ods_ids = explode(',', trim($ods_id,'{}'));

		//asort($ods_ids);
		
		if ( $ods_ids[0] != 0 ) {
			
			$sqlODS = "SELECT id, description, ordem FROM nr_ods ORDER BY ordem";
			$qODS = db_query($sqlODS);

			$ods_list = array();
			while ($r = db_fetch_array($qODS)){
			  $ods_list[$r['id']] = $r['description'];         
			 
			} 
			
			$result ='<ul>';
			
			foreach ($ods_ids as $key => $value) {
						   
					$result.= "<li class= 'nivel'> ".$ods_list[$value]."</li>";
			}
			$result.='</ul>';
			
			format_line("Objetivos de Desenvolvimento Sustentável", $result,  false);
		}
	}
	
  }	

    if (!empty($autor_principal)) { 
      format_line('Autor Principal', $autor_principal);
	}
      
  	format_line("Titulo Principal", $title, false);
  	format_line("Título Variante", $title_en,  false);
  
	format_block("Autoridade Intelectual", $author);
  
	format_block("Palavras-chave[PT]", $keywords);
	format_block("Palavras-chave[EN]", $keywords_en);

	format_block("Resumo", $abstract, false);
   
 
  format_block("Notas", $description);

  format_block("Apresentações do Evento", $event_description); 
 

  format_block("Informações Adicionais", $info);
  echo "<p>\n";
  format_line("Imprenta", $source);
  format_line("Edição", $edicao);
  format_line("Nota versão original", $nota_versao_ori);
  
   format_block("Descrição física", $descricao_fisica);
   format_line("Identificador do objeto digital", html_a($doi,$doi,'blanck'), false);
   format_line("Acesso eletrônico", html_a($acesso_eletronico, $acesso_eletronico,'blanck'), false);
   format_block("Número de livro ou série padrão internacional",  $nlspi);

  
  format_line("Curso", $curso);
  format_line("Disciplina", $disciplina);
  format_line("Professor", $professor);
  format_line("Departamento", $departamento);
 
  echo "<p>\n";

//  format_line(_('Owner'), html_a(get_user($owner_id, 'username'),
//                                 "{$cfg_site}user/?uid=$owner_id"), false);

  format_line("código", $code);
  format_line("Criado por",(get_user($owner_id, 'username')));
  format_line("Criado em", db_locale_date($created));
  format_line("Atualizado em", db_locale_date($updated));
  format_line("Visitas", $visits);
  format_line("Downloads", $downloads);
 
  $acesso = array (0=>"Acesso Aberto (Qualquer pessoa pode acessar o documento sem nenhum tipo de restrição)", 1=>"Acesso Restrito por IP (Apenas à comunidade pode acessar o documento sem nenhum tipo de restrição) " , 2=>"Acesso Restrito(O documento fica com restrições de acesso, somente pessoas autorizadas poderão acessá-lo)");
  format_line("Permissão de acesso ao material ", $acesso[$tacesso]);

echo "</div>";

  if ($remote == 'n') {
		//format_line(_('File name'), $filename);
		$link = $cfg_site.'document/?down='.$code;
		
	if ($format_id == 707) {
		$hora = time();
		$go = 'x'.$hora;
		//  $linkv = $cfg_site.'document/?view='.$code.'&go='.$go;
	    $linkv = $cfg_site.'images/videos/'.$code.'/'.$code.'.mp4';
	  echo '<table id="tabela-bases" cellpadding="0" cellspacing="1">';
	  echo '<tbody>';
	   echo '<tr>';

	   echo '<td>';
       echo '<video id="myVideo" oncontextmenu="return false;"  width="512" height="380" disablePictureInPicture controls controlsList="nodownload">';
       echo '<source src="'.$linkv.'" type="video/mp4">';
	   echo '</video>'; 
       echo '</td>';
	   echo '</tr>';
	  echo '</table>';
	  echo '<br>'; 
	  
	  
  }
else {
       echo '<table class="tabela-bases" cellpadding="0" cellspacing="1">';
	   echo '<thead>';
	   echo '<th>Nome do Arquivo </th>';
	   echo '<th></th>';
	   echo '<th>Formato</th>';
	   echo '<th>Tamanho </th>';
	   echo '<th></th>';
	   echo '</thead>';
	   echo '<tbody>';
	   echo '<tr>';
	   echo '<td>'. html_a("$filename",$link).'</td>' ;
	   echo '<td> Arquivo Principal</td>' ;
	   echo '<td>'._(get_format($format_id, 'name'))."</td>";
	   echo '<td>'.int_to_size($size)."($size bytes)</td>";
	   
	   echo '<td>'.html_a("Visualizar",$link).'</td>';
	   echo '</tr>';
	   $qsf = db_query("SELECT * FROM supplementary_files WHERE document_id=$did");
  		if (db_rows($qsf)>=1){
  			while ($asf = db_fetch_array($qsf)){
				$link = $cfg_site."document/?down=".$code."&idsf=".$asf['id'];
  	    		 $sizesf = $asf['size'];
				echo '<tr>';
				echo '<td>'. html_a($asf['filename'],$link).'</td>' ;
				echo '<td>Anexo</td>' ;
	   			echo '<td>'. _(get_format($asf['format_id'], 'name'))."</td>";
	  		    echo '<td>'.  int_to_size($sizesf) . " ($size bytes)</td>";
	   			echo '<td>'.  html_a("Visualizar",$link).'</td>';
				echo '</tr>';
			}
		}
	   echo '</tbody>';
	   echo '</table>';
	   echo '<br>';
}

}


}

// Consulta com parâmetros vinculados. A camada de include/db.php só aceita SQL
// já interpolado; enquanto ela não for revista, os dados vindos da requisição
// são vinculados aqui, nunca concatenados na consulta.
function doc_query_params ($sql, $params)
{
	global $db_conn;

	if (!($q = @pg_query_params($db_conn, $sql, $params)))
		fatal("Se você está tendo problemas, por favor entre em contato com os administradores da Biblioteca Digital");
	return $q;
}

// Tamanho descompactado gravado no rodapé do gzip (campo ISIZE), usado para o
// Content-Length do arquivo que será realmente enviado. Devolve FALSE se não
// for possível determiná-lo.
function doc_gzip_length ($file)
{
	$size = false;
	if (($fp = @fopen($file, 'rb')) !== false) {
		if (@fseek($fp, -4, SEEK_END) === 0) {
			$tail = @fread($fp, 4);
			if ($tail !== false && strlen($tail) == 4) {
				$u = unpack('V', $tail);
				$size = $u[1];
			}
		}
		@fclose($fp);
	}
	return $size;
}

// Controle de acesso ao download, feito aqui e não em include/control.php:
// check_administrator_rights() devolve normalmente (libera) quando não há
// sessão, e check_user_rights() não declara parâmetro algum, descartando o
// tópico que lhe é passado. Esta verificação olha a sessão e topic_users
// diretamente, valendo mesmo que aquele arquivo não tenha sido corrigido.
function check_document_download_rights ($status, $tid)
{
	global $cfg_site;

	// documento arquivado: público, é o que o portal publica
	if ($status == 'a')
		return;

	// os demais estados estão em curadoria e exigem sessão autenticada
	if (empty($_SESSION['suid']) || !isset($_SESSION['slevel']))
		redirect("{$cfg_site}user/login.php?url=" . rawurlencode($_SERVER['REQUEST_URI']));

	// administrador alcança qualquer documento
	if ($_SESSION['slevel'] == ADM_LEVEL)
		return;

	// 'v' aguarda verificação: só a curadoria; 'w' e 'i' também o depositante
	if ($status == 'v')
		$min_level = MNT_LEVEL;
	else if ($status == 'w' || $status == 'i')
		$min_level = USR_LEVEL;
	else
		message($cfg_site, "Documento não encontrado", "failure");

	if (!valid_int($_SESSION['slevel']) || $_SESSION['slevel'] < $min_level)
		message($cfg_site, "Documento não encontrado", "failure");

	// e apenas dentro da coleção a que o documento pertence
	if (!valid_int($tid) || !valid_int($_SESSION['suid']))
		message($cfg_site, "Documento não encontrado", "failure");

	$qt = doc_query_params('SELECT id FROM topic_users WHERE topic_id=$1 AND users_id=$2',
	                       array($tid, $_SESSION['suid']));
	if (!db_rows($qt))
		message($cfg_site, "Documento não encontrado", "failure");
}

function view_document ($code, $force_download, $sfid, $open){
	global $cfg_site, $cfg_dir_archive, $cfg_dir_incoming;

	// find document - Se a variavel $idsf está vazia busca na tabela nr_document caso contrario supplementary_files
	// $code e $sfid vêm da requisição: vão vinculados, nunca concatenados.
	if (empty($sfid))
		$q = doc_query_params('SELECT D.id,D.topic_id,D.status,D.filename,D.size,D.remote,F.type,F.subtype,F.extension,F.compress FROM nr_document D,nr_format F WHERE D.code=$1 AND D.format_id=F.id', array($code));
    else {
    	if (!valid_int($sfid))
    		message($cfg_site, "Parâmetro inválido", "failure");
    	// o anexo tem de pertencer ao documento pedido
    	$q = doc_query_params('SELECT D.id,D.topic_id,D.filename,D.size,D.remote,F.type,F.subtype,F.extension,F.compress,P.topic_id AS parent_topic_id FROM supplementary_files D, nr_format F, nr_document P WHERE D.id=$1 AND D.format_id=F.id AND D.document_id=P.id AND P.code=$2', array($sfid, $code));
    }

	if (!db_rows($q))
	    message($cfg_site, "Documento não encontrado", "failure");

	 $a = db_fetch_array($q);

   if (empty($sfid))
      $status = $a['status'];
    else {
		$qas = doc_query_params('SELECT status FROM  nr_document  WHERE code=$1', array($code));
	    $as = db_fetch_array($qas);
        $status = $as['status'];	
    }
	
	// autoriza antes de qualquer saída: nada é emitido enquanto o direito de ver
	// este documento não estiver decidido. Para anexo vale a coleção do documento
	// dono, e não a gravada no anexo, que pode estar defasada após troca de base.
	check_document_download_rights($status,
	                               empty($sfid) ? $a['topic_id'] : $a['parent_topic_id']);

	// handle remote documents
	if ($a['remote'] == 'y')
		redirect($a['filename']);

	// check document status
	//$filename = $a['filename'];
	//Retira os espaços em brancos do nome do arquivo
	$filename = str_replace(" ","",$a['filename']);
	$filename = str_replace(",","",$filename);

	if ($status == 'v') {
		// document needs verification
		$file = "$cfg_dir_incoming/$filename";
		$compress = 'n'; // output as is
	}
	else if ($status == 'w' || $status == 'i') {
		// document waiting for approval
         if (empty($sfid)){
	   	   $file = "$cfg_dir_incoming/$filename";
		   $compress = 'n';
	     }else{
 	       $file = "$cfg_dir_incoming/S$sfid.{$a['extension']}";
	   
			if ($a['compress'] == 'y')
			$file .= '.gz';
	
			$compress = $a['compress'];
		 }
		
	}
    else if ($status == 'a') {
    	// document archived
	   if (empty($sfid))
	   	   $file = "$cfg_dir_archive/{$a['topic_id']}/{$a['id']}.{$a['extension']}";
	   else
 	       $file = "$cfg_dir_archive/{$a['topic_id']}/S{$a['id']}.{$a['extension']}";
	   
	    if ($a['compress'] == 'y')
			$file .= '.gz';
		$compress = $a['compress'];


	}
	else
		message($cfg_site, "Documento não encontrado", "failure");

	// o caminho resolvido tem de cair dentro dos diretórios configurados
	$path = @realpath($file);
	$dir_archive = @realpath($cfg_dir_archive);
	$dir_incoming = @realpath($cfg_dir_incoming);
	if ($path === false || !is_file($path) ||
	    !(($dir_archive !== false && strpos($path, $dir_archive . '/') === 0) ||
	      ($dir_incoming !== false && strpos($path, $dir_incoming . '/') === 0)))
		message($cfg_site, "Documento não encontrado", "failure");

		// output document
		// descarta a saída pendente para não corromper o corpo binário
		while (ob_get_level() > 0)
			@ob_end_clean();

		if (!$force_download) {
			
		    header("Content-Type: {$a['type']}/{$a['subtype']}");
			header("Content-Disposition: inline; filename=\"".$filename."\"");
			header('Content-Transfer-Encoding: binary');
		    header('Expires: 0');
            header('Cache-Control: must-revalidate');
            header('Pragma: public');
		}
		else {
			header("Content-type: application/octet-stream");
			header("Content-Disposition: attachment; filename=\"".$filename."\"");
		    header('Expires: 0');
            header('Cache-Control: must-revalidate');
            header('Pragma: public');
		}

		if ($compress == 'y') {
			// decompress file on the fly
			$length = doc_gzip_length($path);
			if ($length !== false)
				header("Content-Length: $length");
			@readgzfile($path);
		}
		else {
			// simply output file
			header('Content-Length: ' . filesize($path));
			@readfile($path);
		}
		// finish explicitly
		exit();
}

?>