api_version = '0.1';

$( document ).ready(function() {

    update_api_version();
    update_api_adapters();
    poll_update()
});

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

    $.getJSON('/api/' + api_version + '/hexitec/background_task', function(response) {
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
        url: '/api/' + api_version + '/hexitec/background_task',
        contentType: "application/json",
        data: JSON.stringify({'enable': enabled})
    });
}

function test_button() {
    var enabled = $('#task-enable').prop('checked');
    console.log("Changing enabled " + (enabled ? "true" : "false") + " to " + !(enabled ? "true" : "false"));
    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/hexitec/background_task',
        contentType: "application/json",
        data: JSON.stringify({'enable': !enabled})
    });
}

function filename_button()
{
    var filename = $('#filename-text').prop('value');
/*    console.log("filename_button(), Sample text contains: " + filename ); */

    $.ajax(`api/` + api_version + `/hexitec/test_area`, {
        method: "PUT",
        contentType: "application/json",
        processData: false,
        data: JSON.stringify({'target_text': filename })
    });
    /* Write filename to target_name's text field */
    $('#target-name').html(filename);
}
