api_version = '0.1';

$( document ).ready(function() {

    update_api_version();
    update_api_adapters();
    poll_update()

    $('#myForm').on('click', function () {

        var value = $("[name=radio]:checked").val();

        var noneButton = $('#noneButton').prop('checked');  // Not really needed as add/dis buttons decide
        var addButton = $('#addButton').prop('checked');
        var disButton = $('#disButton').prop('checked');
        var discriminate_enable = false;
        var addition_enable = false;

        // console.log("Value: " + value + " noneButton: " + noneButton + " addButton: " + addButton + " disButton: " + disButton);
        // if (noneButton === true)
        // {
        //     console.log("if identified none");
        // }
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
            url: '/api/' + api_version + '/hexitec/odin_data/charged_sharing',
            contentType: "application/json",
            data: JSON.stringify({"addition": addition_enable})
        });
    
        $.ajax({
            type: "PUT",
            url: '/api/' + api_version + '/hexitec/odin_data/charged_sharing',
            contentType: "application/json",
            data: JSON.stringify({"discrimination": discriminate_enable})
        });
    })

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
    console.log("filename_button(), Sample text contains: " + filename ); 

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

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/reorder`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'width': parseInt(reorder_columns) })
    });
}

function threshold_filename_changed()
{
    var threshold_filename = $('#threshold-filename').prop('value');
    console.log("threshold_filename_changed(), is now: " + threshold_filename);

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/threshold`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'threshold_filename': threshold_filename })
    });
}

function threshold_value_changed()
{
    var threshold_value = $('#threshold-value').prop('value');
    console.log("threshold_value_changed(), is now: " + threshold_value);

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/threshold`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'value': parseInt(threshold_value) })
    });
}

function threshold_mode_changed()
{
    var threshold_mode = $('#threshold-mode').prop('value');
    console.log("threshold_mode_changed(), is now: " + threshold_mode);

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/threshold`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'mode': threshold_mode })
    });
}

function gradients_filename_changed()
{
    var gradients_filename = $('#gradients-filename').prop('value');
    console.log("gradients_filename_changed(), is now: " + gradients_filename);

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/calibration`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'gradients_filename': gradients_filename })
    });
}

function intercepts_filename_changed()
{
    var intercepts_filename = $('#intercepts-filename').prop('value');
    console.log("intercepts_filename_changed(), is now: " + intercepts_filename);

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/calibration`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'intercepts_filename': intercepts_filename })
    });

}

function pixel_grid_size_changed()
{
    var pixel_grid_size = $('#pixel-grid-size-text').prop('value');
    console.log("pixel_grid_size(), text is now: " + pixel_grid_size); 

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/charged_sharing`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'pixel_grid_size': parseInt(pixel_grid_size) })
    });
}

function max_frames_received_changed()
{
    var max_frames_received = $('#max-frames-received-text').prop('value');
    console.log("max_frames_received(), text is now: " + max_frames_received); 

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/histogram`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'max_frames_received': parseInt(max_frames_received) })
    });
}

function bin_start_changed()
{
    var bin_start = $('#bin-start-text').prop('value');
    console.log("bin_start(), text is now: " + bin_start); 

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/histogram`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'bin_start': parseInt(bin_start) })
    });
}

function bin_end_changed()
{
    var bin_end = $('#bin-end-text').prop('value');
    console.log("bin_end(), text is now: " + bin_end); 

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/histogram`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'bin_end': parseInt(bin_end) })
    });
}

function bin_width_changed()
{
    var bin_width = $('#bin-width-text').prop('value');
    console.log("bin_width(), text is now: " + bin_width); 

    $.ajax(`/api/` + api_version + `/hexitec/odin_data/histogram`, {
        method: "PUT",
        contentType: "application/json",
        data: JSON.stringify({'bin_width': parseFloat(bin_width) })
    });
}


// Get (state) from radio button(s) - http://jsfiddle.net/HWfVN/3/ 

