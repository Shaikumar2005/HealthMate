document.addEventListener("DOMContentLoaded", function () {
    const generateReportBtn = document.getElementById("generate-btn");
    const reportContainer = document.getElementById("reportContainer");

    async function generateReport() {
        // ✅ Show a loading spinner
        reportContainer.innerHTML = `<div class="loader"></div>`;

        try {
            const response = await fetch("http://127.0.0.1:5000/generate_report");
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

            const data = await response.json();
            console.log("Report Data:", data);

            if (data.message) {
                reportContainer.innerHTML = `<p>${data.message}</p>`;
            } else {
                const userData = data.user_data;
                const bmi = (userData.weight / ((userData.height / 100) ** 2)).toFixed(1);
                const bmiClass = getBMIStatus(bmi);
                const insights = formatInsights(data.personalized_report || "No insights available.");

                // ✅ Apply structured UI with a table for key insights
                reportContainer.innerHTML = `
                    <div class="report-card">
                        <h2>🩺 Personalized Health Report for <span>${userData.name}</span></h2>
                        <table class="report-table">
                            <tr><td><strong>Age:</strong></td><td>${userData.age} years</td></tr>
                            <tr><td><strong>Weight:</strong></td><td>${userData.weight} kg</td></tr>
                            <tr><td><strong>Height:</strong></td><td>${userData.height} cm</td></tr>
                            <tr><td><strong>BMI:</strong></td>
                                <td class="bmi ${bmiClass}">${bmi} (${bmiStatusText(bmi)})</td></tr>
                            <tr><td><strong>Blood Pressure:</strong></td><td>${userData.blood_pressure}</td></tr>
                            <tr><td><strong>Cholesterol:</strong></td><td>${userData.cholesterol}</td></tr>
                            <tr><td><strong>Sugar Level:</strong></td><td>${userData.sugar_level}</td></tr>
                        </table>
                        <hr>
                        <h3>📌 Key Insights:</h3>
                        <p class="key-insights">${insights}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error("Error fetching report:", error);
            reportContainer.innerHTML = `<p style="color:red;">❌ Error fetching report: ${error.message}</p>`;
        }
    }

    function getBMIStatus(bmi) {
        if (bmi < 18.5) return "underweight";
        if (bmi >= 18.5 && bmi < 24.9) return "healthy";
        if (bmi >= 25 && bmi < 29.9) return "overweight";
        return "obese";
    }

    function bmiStatusText(bmi) {
        if (bmi < 18.5) return "Underweight";
        if (bmi >= 18.5 && bmi < 24.9) return "Healthy Weight";
        if (bmi >= 25 && bmi < 29.9) return "Overweight";
        return "Obese";
    }

    function formatInsights(text) {
        return text.replace(/\*\*/g, "").replace(/#/g, "").replace(/\n/g, "<br>");
    }

    if (generateReportBtn) {
        generateReportBtn.addEventListener("click", generateReport);
    } else {
        console.error("Button with ID 'generate-btn' not found.");
    }
});
