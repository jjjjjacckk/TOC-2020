$(document).ready(function(){
    //參數區----------------------------
	// 主要div
	var main_div_id = "site_cal";
	// 執行的網址
	var baseUrl = "index.php?c=ste11211";
	//----------------------------------
	
	var query=$("#queryform");	             
	var form=$("#"+main_div_id).find('.form');
	var grid=$("#"+main_div_id).find('.grid');
	
	$("#sdate").datepicker({
		 dateFormat: "yy-mm-dd",
		 onSelect: function (dateText, inst) {
         	$("#query_button").click();
		 }
    });
    
    $( "#sdate" ).datepicker( "setDate", new Date());
    
    $("#sport").change(function() {
    	$("#query_button").click();
    });
    
    
    $("#query_button").on("click", function(e){    	
    	if($("#sport").val()!=''){
	    	nowDate=$("#sdate").attr('value');
			var data=query.serialize().replace(/-/g, "");
			$.ajax({
		        type: "POST",
		        url: 'index.php?c=ste11211' + "&m=read",
		        data: "sport=D&sdate=20201223",
		        async:true,  
	            beforeSend:function(){  
			           grid.block({ 
			                  message: '<p>資料處理中，請稍候</p>', 
			                  css: { border: '1px solid ' } 
			           });   
			           $("#query_button").attr('disabled',true);         	      
				 },
			    complete:function(){ 
				      grid.unblock({ fadeOut: 0 });
				      $("#query_button").attr('disabled',false);   
			     },
	       
		        success: function(m){		        
					//載入資料
					print(m)
		            grid.find('.cal_grid_content').html(m);	            
		   	    },
		  	    error:function(XMLHttpRequest, textStatus, errorThrown){
			        alert("抱歉，資料處理失敗!");	
			        $("#query_button").attr('disabled',false);	
		        }
		    });	
		}else{
			if(e.isTrigger==undefined){
	            alert("請選擇類別!");
	        }
		}
    }).click();
    

});