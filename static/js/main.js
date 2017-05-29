$(document).ready(function () {

	$('#viber-checkbox-params').change(function () {
		if (this.checked) {
			//console.logs("SMS");
			$(".viber-media-param").fadeIn('slow');
		}
		else {
		//console.logs("Hide SMS");
			$(".viber-media-param").fadeOut('slow');
		}
	});

	setTimeout(function(){
		$('body').addClass('loaded');
		$('h1').css('color','#222222');
	}, 0);

});

function validate() {
	if (!($('#viber-checkbox-params').is(':checked')) ) {
		if (!checkEmptyFields()) {
			$(".viber-media-param").children().remove();
		}
	}
}

function checkEmptyFields() {
	var values = $("form").find(".markup").map(function(){return $(this).val();}).get();
	if ( $.inArray("", values) > -1 ) {
    	return true;
	}
	else {
		return false;
	}
}

function checkCountPlaceholders(event) {
	var viberText = $('#viber-message').val(),
		smsText = $('#sms-message').val(),
		re =/{\w+}/g,
		found_viber_params = viberText.match(re),
		found_sms_params = smsText.match(re);
	var param = $('#textareamenu_content > .choose_params_viber').children(),
		param_len = param.length-1;
	if (found_viber_params.length == found_sms_params.length && found_sms_params.length === param_len) {
		return true;
	}
	else {
		alert('Не совпадает количество параметров по столбцам в файле');
		event.preventDefault();
		return false;
	}
}

$(function () {
	$('#datetimepicker').datetimepicker({
		locale: 'ru'
	})
});

function readSingleFile(evt) {
    var f = evt.target.files[0];
    if (f) {
      var r = new FileReader();
      r.onload = function(e) {
          var contents = e.target.result;
          var ct = r.result.replace(/"/g, "");
          var line = /[\r\n|\n]+/;
          var delimiter = /[;|,]+/;
          var words = ct.split(line);
          /**************************Create clickable items **************************/
          if (words[0].split(delimiter).length > 1) {
			for (var i=0; i < words[0].split(delimiter).length-1; i++){
				var elem = $("<li class='placeholder-list-item' ></li>");
				$('#textareamenu_content > ul').append(elem.text('Row_'+(i+1)).on('click', addText));
			}
		  }
		  else {
			$(".placeholder-list-item").remove();
		  }
		  /****************************************END*********************************/
          json_data = JSON.stringify(words);
          //$('.btn-submit').click(function() {
		  	if ($("[name='json_data']").length == 1) {
		  		$("[name='json_data']").remove();
		  	}
		  	var input = $("<input>").attr("type", "hidden").attr("name", "json_data").val(json_data);
			$(".form-horizontal").append($(input));
          //});
      }
      r.readAsText(f);
    } else {
      console.log("Failed to load file");
    }
}

document.getElementById('fileinput').addEventListener('change', readSingleFile, false);
