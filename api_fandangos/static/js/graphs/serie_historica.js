function agregarDados(dates, prices, type) {
    let aggregatedData = {};
    
    dates.forEach((date, index) => {
        let data = new Date(date);
        let key;
        if (type === "mensal") {
            key = `${data.getFullYear()}-${(data.getMonth() + 1).toString().padStart(2, '0')}`;
        } else if (type === "semestral") {
            key = `${data.getFullYear()}-${Math.ceil((data.getMonth() + 1) / 6)}`;
        } else {
            key = date; // Semanal mantém a granularidade original
        }

        if (!aggregatedData[key]) {
            aggregatedData[key] = { total: 0, count: 0 };
        }
        aggregatedData[key].total += parseFloat(prices[index]);
        aggregatedData[key].count++;
    });

    let aggregatedDates = Object.keys(aggregatedData).sort();
    let aggregatedPrices = aggregatedDates.map(key => (aggregatedData[key].total / aggregatedData[key].count).toFixed(2));

    return { labels: aggregatedDates, data: aggregatedPrices };
}

function atualizarGraficos() {
    
    
    let tipo = document.getElementById("agregacao").value;
    let etanolData = agregarDados(datasEtanol, precosEtanol, tipo);
    let milhoData = agregarDados(datasMilho, precosMilho, tipo);

    graficoEtanol.data.labels = etanolData.labels;
    graficoEtanol.data.datasets[0].data = etanolData.data;
    graficoEtanol.update();

    graficoMilho.data.labels = milhoData.labels;
    graficoMilho.data.datasets[0].data = milhoData.data;
    graficoMilho.update();
}


function createChart(canvasId, label, labelsData, dataValues, borderColor) {
    var ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labelsData,
            datasets: [{
                label: label,
                data: dataValues.map(preco => parseFloat(preco).toFixed(4)), // Formata os preços
                borderColor: borderColor,
                backgroundColor: borderColor.replace("1)", "0.2)"), // Cor com transparência
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Data' } },
                y: { title: { display: true, text: 'Preço (R$)' } }
            },
            elements: { line: { tension: 0.3 } }
        },
        plugins: [{
            beforeDraw: function(chart) {
                chart.canvas.parentNode.style.height = '400px'; // Define a altura mínima
            }
        }]
    });
}

document.addEventListener("DOMContentLoaded", function () {
    let datasEtanol = JSON.parse(document.getElementById('dados-etanol').textContent);
    let precosEtanol = JSON.parse(document.getElementById('precos-etanol').textContent);
    let datasMilho = JSON.parse(document.getElementById('dados-milho').textContent);
    let precosMilho = JSON.parse(document.getElementById('precos-milho').textContent);


    createChart('graficoEtanol', 'Preço do Etanol (R$/L)', datasEtanol, precosEtanol, 'rgba(75, 192, 192, 1)');
    createChart('graficoMilho', 'Preço do Milho (R$/60kg)', datasMilho, precosMilho, 'rgba(255, 159, 64, 1)');

});
