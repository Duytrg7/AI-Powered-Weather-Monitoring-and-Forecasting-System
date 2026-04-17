document.addEventListener('DOMContentLoaded', () => {
    const chartElement = document.getElementById('chart');
    if (!chartElement) {
        console.error('Canvas Element not found.');
        return;
    }

    const forecastItems = document.querySelectorAll('.forecast-item');
    const forecastUl = document.querySelector('.forecast'); // Lấy trực tiếp thẻ ul chứa danh sách

    if (forecastItems.length === 0 || !forecastUl) {
        console.error('Không tìm thấy danh sách dự báo.');
        return;
    }

    // --- BƯỚC 1: FIX KÍCH THƯỚC CANVAS ---
    // Lấy chiều rộng thực tế mà trình duyệt đã render cho thẻ ul
    const totalWidth = forecastUl.scrollWidth;

    // Ép cứng kích thước cho thẻ canvas (cả thuộc tính attribute lẫn CSS)
    chartElement.width = totalWidth;
    chartElement.style.width = totalWidth + 'px';
    chartElement.height = 45;
    chartElement.style.height = '45px';
    // -------------------------------------

    const ctx = chartElement.getContext('2d');
    const gradient = ctx.createLinearGradient(0, -10, 0, 100);
    gradient.addColorStop(0, 'rgba(250, 0, 0, 1)');
    gradient.addColorStop(1, 'rgba(136, 255, 0, 1)');

    const temps = [];
    const times = [];

    forecastItems.forEach(item => {
        const time = item.querySelector('.forecast-time').textContent;
        const temp = item.querySelector('.forecast-temperatureValue').textContent;
        const hum = item.querySelector('.forecast-humidityValue').textContent;

        if (time && temp && hum) {
            times.push(time);
            temps.push(temp);
        }
    });

    if (temps.length === 0 || times.length === 0) {
        console.error('Temp or time values are missing.');
        return;
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: times,
            datasets: [
                {
                    label: 'Celsius Degrees',
                    data: temps,
                    borderColor: gradient,
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 2,
                },
            ],
        },
        options: {
            // --- BƯỚC 2: TẮT RESPONSIVE CỦA CHART.JS ---
            responsive: false,
            maintainAspectRatio: false,
            // -------------------------------------------
            plugins: {
                legend: {
                    display: false,
                },
            },
            scales: {
                x: {
                    display: false,
                    offset: true,
                    grid: {
                        drawOnChartArea: false,
                    },
                },
                y: {
                    display: false,
                    grid: {
                        drawOnChartArea: false,
                    },
                },
            },
            animation: {
                duration: 750,
            },
            layout: {
                padding: {
                    left: 0,
                    right: 0
                }
            }
        },
    });
});