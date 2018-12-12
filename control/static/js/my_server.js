api_version = '0.1';

$( document ).ready(function() {

    update_api_version();
    update_api_adapters();
    poll_update()
    
    $('#myForm').on('click', function () {
        var value = $("[name=radio]:checked").val();

        var noneButton = $('#noneButton').prop('checked');
        var addButton = $('#addButton').prop('checked');
        var disButton = $('#disButton').prop('checked');
        var discriminate_enable = false;
        var addition_enable = false;

        console.log("Value: " + value + " noneButton: " + noneButton + " addButton: " + addButton + " disButton: " + disButton);
        if (noneButton === true)
        {
            console.log("if identified none");
        }
        if (addButton === true)
        {
            console.log("if identified add");
            addition_enable = true;
        }
        if (disButton === true)
        {
            console.log("if identified dis");
            discriminate_enable = true;
        }

        $.ajax({
            type: "PUT",
            url: '/api/' + api_version + '/mxt/my_data/charged_sharing',
            contentType: "application/json",
            data: JSON.stringify({"addition": addition_enable})
        });
    
        $.ajax({
            type: "PUT",
            url: '/api/' + api_version + '/mxt/my_data/charged_sharing',
            contentType: "application/json",
            data: JSON.stringify({"discrimination": discriminate_enable})
        });
    
    })

    // $("input[name='type']:radio").change(function(){
    //     if($(this).val() == '1')
    //     {
    //       // do something
    //     }
    //     else if($(this).val() == '2')
    //     {
    //       // do something
    //     }
    //     else if($(this).val() == '3')
    //     {
    //       // do something
    //     }
    // });    

    // Respond to user selecting either/none of CS algorithm options
    // $('button').on('click', function () {
    //     console.log('hi');
    //     handleCsRadioButtons($(this).is("#noneButton") && !$(this).is("#noneButton.active"),
    //     $(this).is("#addButton") && !$(this).is("#addButton.active"),
    //                  !$(this).is('#noneButton')&&!$(this).is('#addButton'));
    // });
});

function handleCsRadioButtons(noneButton, addition_enable, discriminate_enable) {

    var api_url = '/api/0.1/';    //'/api/0.1/live_view/';
    var my_data_url = api_url + 'mxt/my_data/';

    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/mxt/my_data/charged_sharing',
        contentType: "application/json",
        data: JSON.stringify({"addition": addition_enable})
    });

    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/mxt/my_data/charged_sharing',
        contentType: "application/json",
        data: JSON.stringify({"discrimination": discriminate_enable})
    });


    // var modifyValueCount = $("button[id=editButton].active").length;
    // var copyValueCount = $("button[id=copyButton].active").length;
    // if(noneButton){
    //     modifyValueCount++;
    //     copyValueCount--;
    // }
    // if(addButton){
    //     copyValueCount++;
    //     modifyValueCount--;
    // }
    // if(decrementAll){
    //     copyValueCount--;
    //     modifyValueCount--;
    // }

    // $("#variablesToModifyCount").text(modifyValueCount < 0 ? 0 : modifyValueCount);
    // $("#variablesToCopyCount").text(copyValueCount < 0 ? 0 : copyValueCount);
}

function poll_update() {
/*    update_background_task(); */
    setTimeout(poll_update, 500);   
}

function update_api_version() {

    $.getJSON('/api', function(response) {
        $('#api-version').html(response.api_version);
        api_version = response.api_version;
    });
}

function update_api_adapters() {

    $.getJSON('/api/' + api_version + '/adapters/', function(response) {
        adapter_list = response.adapters.join(", ");
        $('#api-adapters').html(adapter_list);
    });
}

function update_background_task() {

    $.getJSON('/api/' + api_version + '/mxt/background_task', function(response) {
        var task_count = response.background_task.count;
        var task_enabled = response.background_task.enable;
        $('#task-count').html(task_count);
        $('#task-enable').prop('checked', task_enabled);
    });
}

function change_enable() {
    var enabled = $('#task-enable').prop('checked');
    console.log("Enabled changed to " + (enabled ? "true" : "false"));
    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/mxt/background_task',
        contentType: "application/json",
        data: JSON.stringify({'enable': enabled})
    });
}

function test_button() {
    var enabled = $('#task-enable').prop('checked');
    console.log("Changing enabled " + (enabled ? "true" : "false") + " to " + !(enabled ? "true" : "false"));
    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/mxt/background_task',
        contentType: "application/json",
        data: JSON.stringify({'enable': !enabled})
    });
}

function filename_button()
{
    var filename = $('#filename-text').prop('value');
/*    console.log("filename_button(), Sample text contains: " + filename ); */

    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + `/mxt/test_area`,
        contentType: "application/json",
        data: JSON.stringify({'target_text': filename })
    });
    /* Write filename to target_name's text field */
    $('#target-name').html(filename);
}

function reorder_rows_changed()
{
    var reorder_rows = $('#rows-text').prop('value');
    console.log("reorder_rows(), text is now: " + reorder_rows); 

    // dodgy: - update me..
    $.ajax(`/api/` + api_version + `/mxt/my_data/reorder`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'height': parseInt(reorder_rows) })
    });
}

function reorder_columns_changed()
{
    var reorder_columns = $('#columns-text').prop('value');
    console.log("reorder_columns(), text is now: " + reorder_columns); 

    // var api_url = '/api/0.1/';    //'/api/0.1/live_view/';
    // var live_view_url = api_url + 'live_view/';
    // var my_data_url = api_url + 'mxt/my_data/';

    // dodgy: - update me..
    $.ajax(`/api/` + api_version + `/mxt/my_data/reorder`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'width': parseInt(reorder_columns) })
    });
}


// Get (state) from radio button(s) - http://jsfiddle.net/HWfVN/3/ 
// $(document).ready(function () {
//     // $("#variablesToModifyCount").text($("button[id=editButton].active").length);
//     // $("#variablesToCopyCount").text($("button[id=copyButton].active").length);

//     // $('button').on('click', function () {
//     //     console.log('hi');
//     //     updateCounts($(this).is("#editButton") && !$(this).is("#editButton.active"),
//     //     $(this).is("#copyButton") && !$(this).is("#copyButton.active"),
//     //                  !$(this).is('#editButton')&&!$(this).is('#copyButton'));
//     // });

// });

$(document).ready(function () {
    $("#variablesToModifyCount").text($("button[id=editButton].active").length);
    $("#variablesToCopyCount").text($("button[id=copyButton].active").length);

    $('button').on('click', function () {
        updateCounts($(this).is("#editButton") && !$(this).is("#editButton.active"),
        $(this).is("#copyButton") && !$(this).is("#copyButton.active"),
                     !$(this).is('#editButton')&&!$(this).is('#copyButton'));
    });


});

function updateCounts(incrementEdit, incrementCopy, decrementAll) {
    var modifyValueCount = $("button[id=editButton].active").length;
    var copyValueCount = $("button[id=copyButton].active").length;
    if(incrementEdit){
        modifyValueCount++;
        copyValueCount--;
    }
    if(incrementCopy){
        copyValueCount++;
        modifyValueCount--;
    }
    if(decrementAll){
        copyValueCount--;
        modifyValueCount--;
    }

    $("#variablesToModifyCount").text(modifyValueCount < 0 ? 0 : modifyValueCount);
    $("#variablesToCopyCount").text(copyValueCount < 0 ? 0 : copyValueCount);
}