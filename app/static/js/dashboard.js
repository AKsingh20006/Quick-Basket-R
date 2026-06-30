const salesCanvas = document.getElementById("salesTrendChart");

if (salesCanvas && window.Chart) {
    const labels = JSON.parse(salesCanvas.dataset.labels || "[]");
    const values = JSON.parse(salesCanvas.dataset.values || "[]");
    const context = salesCanvas.getContext("2d");
    const gradient = context.createLinearGradient(0, 0, 0, 260);

    gradient.addColorStop(0, "rgba(37, 99, 235, 0.24)");
    gradient.addColorStop(1, "rgba(37, 99, 235, 0)");

    new Chart(salesCanvas, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Revenue",
                data: values,
                borderColor: "#2563eb",
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                pointBackgroundColor: "#ffffff",
                pointBorderColor: "#2563eb",
                pointBorderWidth: 2,
                pointRadius: 4,
                tension: 0.38,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return "Revenue: Rs. " + Number(context.parsed.y || 0).toFixed(2);
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                    },
                    ticks: {
                        color: "#667085",
                    },
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: "rgba(102, 112, 133, 0.14)",
                    },
                    ticks: {
                        color: "#667085",
                        callback: function (value) {
                            return "Rs. " + value;
                        },
                    },
                },
            },
        },
    });
}
