/**
 * Created by rhcpist on 13.04.17.
 */

$(document).ready(function(){

    setTimeout(function(){
		$('body').addClass('loaded');
		$('h1').css('color','#222222');
	}, 0);

    $('#datatable').DataTable({
        "pageLength": 20,
        "order": [1, 'desc']
    });
});

