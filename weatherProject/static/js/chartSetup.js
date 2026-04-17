document.addEventListener('DOMContentLoaded', () => {
    const chartElement = document.getElementById('chart');
    const forecastUl = document.querySelector('.forecast');
    const forecastItems = document.querySelectorAll('.forecast-item');

    if (!chartElement || !forecastUl || forecastItems.length === 0) return;

    // 1. ÉP KÍCH THƯỚC CANVAS ĐÚNG BẰNG ĐỘ DÀI CỦA KHUNG CHỨA (UL)
    const totalWidth = forecastUl.scrollWidth;
    chartElement.width = totalWidth;
    chartElement.style.width = totalWidth + 'px';
    chartElement.height = 45;
    chartElement.style.height = '45px';

    const ctx = chartElement.getContext('2d');
    const gradient = ctx.createLinearGradient(0, -10, 0, 100);
    gradient.addColorStop(0, 'rgba(250, 0, 0, 1)');
    gradient.addColorStop(1, 'rgba(136, 255, 0, 1)');

    const temps = [];
    const times = [];

    forecastItems.forEach(item => {
        const time = item.querySelector('.forecast-time').textContent;
        const temp = item.querySelector('.forecast-temperatureValue').textContent;

        if (time && temp) {
            times.push(time);
            temps.push(temp);
        }
    });

    // 2. TÍNH TOÁN ĐỘ LỆCH ĐỂ DỊCH BIỂU ĐỒ (Dựa trên ý tưởng của bạn)
    const ITEM_WIDTH = 90; // Trùng với min-width: 90px trong CSS
    const HALF_ITEM = ITEM_WIDTH / 2; // 45px - Khoảng cách từ lề đến tâm điểm

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: times,
            datasets: [{
                label: 'Celsius Degrees',
                data: temps,
                borderColor: gradient,
                pointBackgroundColor: gradient,
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
            }],
        },
        options: {
            responsive: false,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    left: HALF_ITEM + 20,
                    right: HALF_ITEM + 9,
                }
            },
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: {
                    display: false,
                    // QUAN TRỌNG: Phải set offset là false để vô hiệu hóa khoảng cách thừa mặc định của Chart.js
                    offset: false,
                    grid: { drawOnChartArea: false },
                },
                y: {
                    display: false,
                    grid: { drawOnChartArea: false },
                },
            },
            animation: { duration: 750 },
        },
    });
});