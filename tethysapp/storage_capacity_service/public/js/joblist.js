 $(document).ready(function () {
     $('#job-table').DataTable(  {
        "order": [[ 1, "asc" ]]
    });
     var chart_options =
     {
        chart: {
            renderTo: 'sc_chart',
            zoomType: 'x'
        },
            loading: {
                labelStyle: {
                    top: '100%',
                    left: '100%',
                    display: 'block',
                    width: '100px',
                    height: '100px',
                    backgroundColor: '#000'
                }
            },
        title: {
            text: 'Storage Capacity Curve'
        },
        xAxis: {
            title: {
                text: 'Storage(m3)'
            }
            },
        yAxis: {
            title: {
                text: 'Elevation(m)'
            }
            },
        legend: {
            enabled: true
        },
        series: [{}]

        };

        chart_options.series[0].type = 'line';
        chart_options.series[0].name = 'Elevation-Storage';

        chart = new Highcharts.Chart(chart_options);

        });


 function cancel_delete_job(jobid)
 {

     $.ajax({
        type: 'GET',
        url: '/apps/storage-capacity-service/stop/',
        dataType:'json',
        data: {
                'jobid': jobid,

                },
        success: function (data) {

                if (data.status == "success")
                {
                    var removed_row_from_job_table = $('#job-table').DataTable().row('#' + jobid);
                    removed_row_from_job_table.remove().draw(false);
                }
                else
                {
                    alert("Failed to cancel/delete this job!");
                }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            alert("Failed to cancel/delete this job!");
        }
    });
 }

 function draw(jobid) {

    $.ajax({
        type: 'GET',
        url: '/apps/storage-capacity-service/get/',
        dataType:'json',
        data: {
                'jobid': jobid
                },
        success: function (data) {

                if (data.status == "success" && data.job_status == "success")
                {
                    chart.series[0].setData(data.job_result.storage_list);
                }
                else
                {
                    alert("Failed to view this result!");
                }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            alert("Failed to view this result!");
        }
    });
}

