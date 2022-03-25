const add_years = (year_start, year_end) => {
    let y_arr = []
    for (let i = year_start; i <= year_end; i++) {
        y_arr.push([i.toString()])
    }
    return y_arr
}

const drawChartIncomes = (rows) => {

    let data = new google.visualization.DataTable();
    data.addColumn('string', 'years');
    data.addColumn('number', 'High income');
    data.addColumn('number', 'Upper middle income');
    data.addColumn('number', 'Lower middle income');
    data.addColumn('number', 'Low income');

    data.addRows(rows);

    let options = {
        chart: {
            title: 'Net primary school enrollment, by income group (%)',
            subtitle: 'Low- and middle-income countries are closing the gap with high-income countries in school enrollment rates'
        },
        lineWidth: 5,
        interpolateNulls: true,
        width: 900,
        height: 500,
        theme: 'material',
    };

    let chart = new google.visualization.LineChart(document.getElementById('line-chart'));

    chart.draw(data, options);
}

const drawChartFemaleIntake = (rows) => {

    let data = new google.visualization.DataTable();
    data.addColumn('string', 'years');
    data.addColumn('number', 'female intake');

    data.addRows(rows);

    let options = {
        chart: {
            title: 'Female-intake',
            subtitle: 'Female intake non è vero perchè se lo fossi non avresti bisogno della conferma altrui.'
        },
        lineWidth: 4,
        interpolateNulls: true,
        width: 1000,
        height: 600,
        theme: 'material'
    };

    let chart = new google.visualization.LineChart(document.getElementById('line-chart3'));

    chart.draw(data, options);
}

$.get('/api/education/school-enrollment-primary-by-income-group/all', (response) => {
    let rows = add_years(1960, 2020)
    response.forEach(e => {
      e['years'].forEach(k => {
          rows[e['years'].indexOf(k)].push(k['sc_enr_primary'])
      })
    })

    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(() => {drawChartIncomes(rows)})
})


$.get('/api/education/female-intake/country-by-code/wld', (response) => {
    let rows = add_years(2005, 2018)
    response.forEach(e => {
        rows[response.indexOf(e)].push(parseFloat(e['female_intake'].toString().splice(2, '.')))
    })

    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(() => {drawChartFemaleIntake(rows, 'line-chart3')})
})



$.get('/api/education/school-enrollment-primary/country-by-code/wld', (data) => {
    window.arr = [
        ['year', 'WORLD']
    ]
    for (let year of data) {
        arr.push([year['year'].toString(), parseFloat(year['sc_enr_primary'].toString().splice(2, '.'))])
    }

    const lineChart = {
        chart: null,
        data: arr,
        element: '#line-chart2',
        options: {
            title: 'School enrollment, primary (% net)',
            width: 900,
            height: 700
        },
        interpolateNulls: true,
    }

    const init = () => {
        lineChart.chart = new google.visualization.LineChart(
            document.querySelector(lineChart.element)
        )
            lineChart.chart.draw(
            google.visualization.arrayToDataTable(lineChart.data),
            lineChart.options
        )
    }

    google.charts.load('current', {
        packages: ['corechart'],
        callback: init
    })
})