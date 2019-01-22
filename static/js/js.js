

////////////////////////////////////////////////////////

var fileName = '';
var fileData;
var csvfile;
function readUrl(input) {
  if (input.files && input.files[0]) {
    let reader = new FileReader();
    reader.onload = (e) => {
      fileData = input.files[0];
      fileName = input.files[0].name;
      csvfile = input.files[0];
      if(fileName!='') {
        $("#file_input_div").html(fileName);
        input.setAttribute("data-title", fileName);
        $("#upload-btn").prop('disabled', false);
      }
    }
    reader.readAsDataURL(input.files[0]);
  }
}

$(function() {
  $("#upload-btn").click(function() {
    if ($('#email').val() =="") {
        alert("input your email address!");
        return;
    }
    var fd = new FormData();
    fd.append('file', csvfile, fileName);
    fd.append('email', $('#email').val());
    $('#inputFile').val('');
    $('#email').val('');
    $.ajax({
      url: '/upload',
      method: 'POST',
      data: fd,
      processData: false,
      contentType: false,
      mimeType: "multipart/form-data",
      success: function(res) {
        let result = JSON.parse(res);
        $("#result_data").attr("style", "display:block;");
        $("#result_data_err").attr("style", "display: none;");
        alert(result.result);
      }
    });
  });
})
