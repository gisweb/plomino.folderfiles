(function ($) {
    "use strict";


    $(function () {

        var my_config_upload_form  = function (options) {

            //we have to check if the fileupload element existing

            console.log(options)

            if ($('#fileupload')[0] !== undefined) {
                console.log(jupload.config['extensions'])
                var files_re = new RegExp('(\\.|\/)('+jupload.config['extensions']+')$', 'i');
                if(options["extensions"])
                  files_re = new RegExp('(\\.|\/)('+options['extensions']+')$', 'i');
                var maxFileSize = jupload.config['max_file_size'];
                if(options["maxfilesize"])
                  maxFileSize = options["maxfilesize"];
                // Initialize the jQuery File Upload widget:
                $('#fileupload').fileupload({'sequentialUploads':true, 'singleFileUploads':true});

                // Enable iframe cross-domain access via redirect option:
                $('#fileupload').fileupload(
                    'option',
                    'redirect',
                    window.location.href.replace(
                        /\/[^\/]*$/,
                        '/cors/result.html?%s'
                    )
                );

                $('#fileupload').fileupload('option', {
                    url: '',
                    maxFileSize: maxFileSize,
                    acceptFileTypes: files_re,
                    process: [
                        {
                            action: 'load',
                            fileTypes: files_re,
                            maxFileSize: maxFileSize
                        },
                        {
                            action: 'resize',
                            maxWidth: jupload.config['resize_max_width'],
                            maxHeight: jupload.config['resize_max_height']
                        },
                        {
                            action: 'save'
                        }
                    ],
                    start_i18n: jupload.messages['START_MSG'],
                    cancel_i18n: jupload.messages['CANCEL_MSG'],
                    delete_i18n: jupload.messages['DELETE_MSG'],
                    description_i18n: jupload.messages['DESCRIPTION_MSG'],
                    error_i18n: jupload.messages['ERROR_MSG']
                });
                console.log ($('#fileupload').fileupload());
                // Upload server status check for browsers with CORS support:
                if ($.support.cors) {
                    $.ajax({
                        url: './',
                        type: 'HEAD'
                    }).fail(function () {
                        $('<span class="alert alert-error"/>')
                            .text('Upload server currently unavailable - ' +
                                    new Date())
                            .appendTo('#fileupload');
                    });
                }

                // main settings:
                // var files_re = new RegExp('(\\.|\/)('+jupload.config['extensions']+')$', 'i');
                // $('#fileupload').fileupload('option', {
                //     maxFileSize: jupload.config['max_file_size'],
                //     acceptFileTypes: files_re,
                //     resizeMaxWidth: jupload.config['resize_max_width'],
                //     resizeMaxHeight: jupload.config['resize_max_height']
                // });
                // // Upload server status check for browsers with CORS support:
                // if ($.support.cors) {
                //     $.ajax({
                //         url:'',
                //         type: 'HEAD'
                //     }).fail(function () {
                //         $('<span class="alert alert-error"/>')
                //             .text('Upload server currently unavailable - ' +
                //                     new Date())
                //             .appendTo('#fileupload');
                //     });
                // }

                // //in the latest version we have a method formData who actually is
                // // doing this...=)
                $('#fileupload')
                  .bind('fileuploadsubmit', function (e, data) {
                      var inputs;
                      if(data.context){
                          inputs = data.context.find(':input');
                      }else{
                          inputs = data.form.find(':input');
                      }
                      if (inputs.filter('[required][value=""]').first().focus().length) {
                          return false;
                      }
                      data.formData = inputs.serializeArray();
                    })
                  .bind('fileuploadalways', function (e, data) {
                    console.log("DDDDDDDDDDDDd")
                    //boh...
                  })
                  .bind('fileuploaddone', function (e, data) {
                    console.log(data.context.first(".preview"))
                    console.log(data.files)
                    if(data.files.length){
                      var ftype = data.files[0].type
                      if (ftype=="application/pdf"){
                        //SOSTITUIRE CON IMMAGINE PDF
                        console.log(data.context)
                      }

                    }

                    console.log(data.result.files)
                    //elenco legato al campo
                    var info = data.result.files[0]
                    console.log(info)
                    var $el = $("#"+info["field_name"]+"-list");
                    console.log($el)

                    
                    $el.append(
                        $('<li>').append(
                            $('<a>').attr('href',info["url"]).append(
                                $('<span>').attr('class', 'tab').append(info["name"])
                    )));   



         

                  });

                $(document).bind('drop', function (e) {
                    var url = $(e.originalEvent.dataTransfer.getData('text/html')).filter('img').attr('src');
                    if (url) {
                        $.getImageData({
                            url: url,
                            server:'http://localhost:8080/Plone/@@jsonimageserializer?callback=?',
                            success: function (img) {
                                var canvas = document.createElement('canvas');
                                canvas.width = img.width;
                                canvas.height = img.height;
                                if (canvas.getContext && canvas.toBlob) {
                                    canvas.getContext('2d').drawImage(img, 0, 0, img.width, img.height);
                                    canvas.toBlob(function (blob) {
                                        $('#fileupload').fileupload('add', {files: [blob]});
                                    }, "image/jpeg");
                                }
                            },
                            error: function(xhr, text_status){
                                // Handle your error here
                            }
                        });
                    }
                    e.preventDefault();
                });

            }

        };


//        TODO
//        da fare per ogni campo che ha plugin directupload


        //overlay collective.upload

      $('.iol-upload-doc, .iol-multi-upload-doc').bind("click",function(e){

        e.preventDefault();

        var fieldName = $(this).attr("name")

        var options = {};
        //if ($(this).data("maxsize"))
          //options["maxsize"] = $(this).parent()

        options = $(this).data()

        console.log(options)


        if ($(this).hasClass("iol-upload-doc") && $("#"+fieldName+"-list").find("li").length >0){
            //possiamo anche mettere il nome del file nell'avviso!!
            if (!confirm("Attenzione, il campo prevede un solo allegato. Se si allega un nuovo file, il file attuale verrÃ  rimosso e sostituito"))
                return


        }



        



        $(this).parent().prepOverlay(
                    {
                        subtype: 'ajax',
                        filter: common_content_filter,
                        config: {
                            onLoad: function(arg){
                                my_config_upload_form(options);
                            }
                        }
                    }
                );

      })


      $(".iol-wait-doc").each(function(index){

            var fieldName = $(this).attr("name");

            //if(typeof(iol_document_url)=='undefined')
                //return;
            
            //var serviceUrl = iol_document_url + "/createdocx";
            var serviceUrl = $(this).data("serviceUrl");
            var group = $(this).data("group");
            var model = $(this).data("model");
            var pdf = $(this).data("pdf") || 0;
            var printForm = $(this).data("printform") || '';

            var data={
                "field":fieldName,
                "model":model,
                "grp":group,
                "pdf":pdf,
                "printForm":printForm
            }

            $.ajax({
                'url':serviceUrl,
                'type':'GET',     
                'data':data,
                'dataType':'JSON',     
                'success':function(data, textStatus, jqXHR){
                  console.log(data)

                    $("#" + fieldName + "-createdoc").removeClass("iol-wait-doc");
                    $("#" + fieldName + "-createdoc").addClass("iol-download-doc");
                    $("#" + fieldName + "-download").attr("href","getfile?filename=" + data.fileName)


                } 
            })



      });
  
    });
})(jQuery);

