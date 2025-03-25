document.getElementById("fraudForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const transaction_id = document.getElementById("transaction_id").value;
    const amount = document.getElementById("amount").value;
    const location = document.getElementById("location").value;
    const features = document.getElementById("features").value.split(",").map(Number);

    const response = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transaction_id, amount, location, features })
    });

    const result = await response.json();
    document.getElementById("result").innerText = `Prediction: ${result.prediction} \n Confidence: ${result.confidence}`;

    if (result.alert) {
        alert(result.alert);
    }
});
