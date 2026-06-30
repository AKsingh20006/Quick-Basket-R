const monthlyCanvas = document.getElementById("monthlySalesChart");

if (monthlyCanvas && window.Chart) {
    new Chart(monthlyCanvas, {
        type: "bar",
        data: {
            labels: JSON.parse(monthlyCanvas.dataset.labels || "[]"),
            datasets: [{
                label: "Revenue",
                data: JSON.parse(monthlyCanvas.dataset.values || "[]"),
                backgroundColor: "#2563eb",
                borderRadius: 6,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: "#667085" } },
                y: {
                    beginAtZero: true,
                    grid: { color: "rgba(102, 112, 133, 0.14)" },
                    ticks: {
                        color: "#667085",
                        callback: function (value) {
                            return "₹" + value;
                        },
                    },
                },
            },
        },
    });
}
