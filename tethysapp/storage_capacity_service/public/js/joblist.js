 $(document).ready(function () {
            var chart_options = {
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

        function draw(jobid) {

            $.ajax({
                type: 'GET',
                url: '/apps/storage-capacity-service/get/',
                dataType:'json',
                data: {
                        'jobid': jobid,

                        },
                success: function (data) {

                        if (data.STATUS == "success")
                        {
                            chart.series[0].setData(data.SC_RESULT);
                        }


                },
                error: function (jqXHR, textStatus, errorThrown) {
                    alert("Error");
                    debugger;
                    $('#hydroshare-proceed').prop('disabled', false);
                    console.log(jqXHR + '\n' + textStatus + '\n' + errorThrown);
                    displayStatus.removeClass('uploading');
                    displayStatus.addClass('error');
                    displayStatus.html('<em>' + errorThrown + '</em>');
                }
            });
}

