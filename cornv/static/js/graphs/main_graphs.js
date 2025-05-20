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
