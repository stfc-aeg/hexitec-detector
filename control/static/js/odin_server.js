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

    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + `/hexitec/test_area`,
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
    $.ajax(`/api/` + api_version + `/hexitec/odin_data/reorder`, {
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
    // var odin_data_url = api_url + 'hexitec/odin_data/';

    // dodgy: - update me..
    $.ajax(`/api/` + api_version + `/hexitec/odin_data/reorder`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'width': parseInt(reorder_columns) })
    });
}
