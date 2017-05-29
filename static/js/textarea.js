function count_sms(sms) {

	inputStr = sms.value;
	strlength= inputStr.length;
	lat = inputStr.search(/^[\x20-\x7f\x0a\x0d\u20AC\u00D6\u00A3\u00A5\u00E8\u00E9\u00F9\u00EC\u00F2\u00C7\u00D8\u00F8\u00C5\u00E5\u0394\u0394\u03A6\u0393\u039B\u03A9\u03A0\u03A8\u03A3\u0398\u00C6\u039E\u00E6\u00DF\u00C9\u00A4\u00C4\u00D6\u00D1\u00DC\u00A7\u00BF\u00E4\u00F6\u00F1\u00FC\u00E0]*$/);
	var sbc=0; var ss=0;
	var smscnt=1;
	while (inputStr.indexOf("\x0d\x0A", ss)>-1) { sbc++; ss=1+inputStr.indexOf("\x0d\x0A", ss); }
	if (lat==0)
	{

	var twobyte=new Array('^','{','}','_','\\',
		'[','~',']','|',"\u20AC",
		"\u00D6","\u00A3","\u00A5",
		"\u00E8","\u00E9","\u00F9",
		"\u00EC","\u00F2","\u00C7",
		"\u00D8","\u00F8","\u00C5",
		"\u00E5","\u0394","\u03A6",
		"\u0393","\u039B","\u03A9",
		"\u03A0","\u03A8","\u03A3",
		"\u0398","\u039E","\u00C6",
		"\u00E6","\u00DF","\u00C9",
		"\u00A4","\u00C4","\u00D6",
		"\u00D1","\u00DC","\u00A7",
		"\u00BF","\u00E4","\u00F6",
		"\u00F1","\u00FC","\u00E0"
		);


		var tbc=0;
		for (i=0; i<twobyte.length; i++)
		{
		 var sc=twobyte[i];
		 var ss=0;
		 while (inputStr.indexOf(sc, ss)>-1) { tbc++; ss=1+inputStr.indexOf(sc, ss); }
		}
		len = strlength + tbc - sbc;
		if (len>160) {smscnt=Math.ceil(len/153);}
	}
	else
	{
		len = strlength - sbc;
		if (len>70) {smscnt=Math.ceil(len/67);}
	}
	$('#count_message').html('Количество частей в SMS: ' + smscnt);
	$('#count_symbols').html('Количество символов: ' + len);
	//sms.focus();
};


function count_viber(textarea) {
    var text_max = 999;
    var text_length = textarea.value.length;
    var text_remaining = text_max - text_length;
    $('#viber-help-block').html('Символов осталось: ' +text_remaining);
}

function addText(event) {
    var targ = event.target || event.srcElement;
    var par = $(event.target).parent().hasClass( "choose_params_viber" );
    if (par === true) {
    	document.getElementById("viber-message").value += '{' + targ.textContent + '}' || targ.innerText;
	}
	else {
    	document.getElementById("sms-message").value += '{' + targ.textContent + '}' || targ.innerText;
	}

}