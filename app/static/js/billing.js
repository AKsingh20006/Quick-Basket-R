function money(value) {
    return "₹" + Number(value || 0).toFixed(2);
}

function recalculateBilling() {
    let subtotal = 0;

    document.querySelectorAll(".cart-row").forEach(function (row) {
        const productSelect = row.querySelector(".product-select");
        const quantityInput = row.querySelector(".quantity-input");
        const lineTotalInput = row.querySelector(".line-total");
        const selectedOption = productSelect.options[productSelect.selectedIndex];
        const price = Number(selectedOption ? selectedOption.dataset.price || 0 : 0);
        const stock = Number(selectedOption ? selectedOption.dataset.stock || 0 : 0);
        const quantity = Math.max(Number(quantityInput.value || 0), 0);
        const safeQuantity = stock > 0 ? Math.min(quantity, stock) : quantity;

        if (quantity !== safeQuantity) {
            quantityInput.value = safeQuantity;
        }

        const lineTotal = price * safeQuantity;
        subtotal += lineTotal;
        lineTotalInput.value = money(lineTotal);
    });

    const discount = Number(document.getElementById("discount_amount")?.value || 0);
    const gstPercent = Number(document.getElementById("gst_percent")?.value || 0);
    const taxable = Math.max(subtotal - discount, 0);
    const gst = taxable * gstPercent / 100;
    const total = taxable + gst;

    document.getElementById("subtotalPreview").textContent = money(subtotal);
    document.getElementById("gstPreview").textContent = money(gst);
    document.getElementById("totalPreview").textContent = money(total);

    const amountPaid = document.getElementById("amount_paid");
    if (amountPaid && !amountPaid.dataset.touched) {
        amountPaid.value = total.toFixed(2);
    }
}

function bindCartRow(row) {
    row.querySelectorAll("select, input").forEach(function (input) {
        input.addEventListener("input", recalculateBilling);
        input.addEventListener("change", recalculateBilling);
    });

    row.querySelector(".remove-cart-row").addEventListener("click", function () {
        const rows = document.querySelectorAll(".cart-row");
        if (rows.length > 1) {
            row.remove();
            recalculateBilling();
        }
    });
}

document.querySelectorAll(".cart-row").forEach(bindCartRow);

document.getElementById("addCartRow")?.addEventListener("click", function () {
    const firstRow = document.querySelector(".cart-row");
    const clone = firstRow.cloneNode(true);
    clone.querySelector(".product-select").value = "";
    clone.querySelector(".quantity-input").value = "1";
    clone.querySelector(".line-total").value = money(0);
    document.getElementById("cartRows").appendChild(clone);
    bindCartRow(clone);
});

document.getElementById("amount_paid")?.addEventListener("input", function (event) {
    event.target.dataset.touched = "true";
});

document.getElementById("customer_id")?.addEventListener("change", function (event) {
    const option = event.target.options[event.target.selectedIndex];
    document.getElementById("customer_name").value = option.dataset.name || "";
    document.getElementById("customer_phone").value = option.dataset.phone || "";
});

["discount_amount", "gst_percent"].forEach(function (id) {
    document.getElementById(id)?.addEventListener("input", recalculateBilling);
});

const billingCanvas = document.getElementById("billingSalesChart");
if (billingCanvas && window.Chart) {
    new Chart(billingCanvas, {
        type: "bar",
        data: {
            labels: JSON.parse(billingCanvas.dataset.labels || "[]"),
            datasets: [{
                label: "Revenue",
                data: JSON.parse(billingCanvas.dataset.values || "[]"),
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
                        callback: function (value) { return "₹" + value; },
                    },
                },
            },
        },
    });
}

recalculateBilling();
