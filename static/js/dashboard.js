document.addEventListener("DOMContentLoaded", function () {
    const malesCount = JSON.parse(document.getElementById('malesCount').textContent);
    const femalesCount = JSON.parse(document.getElementById('femalesCount').textContent);

    // Traffic Chart
    const trafficCtx = document.getElementById('traffic').getContext('2d');
    const trafficChart = new Chart(trafficCtx, {
        type: 'line',
        data: {
            labels: [
                gettext('January'),
                gettext('February'),
                gettext('March'),
                gettext('April'),
                gettext('May'),
                gettext('June'),
                gettext('July'),
                gettext('August'),
                gettext('September'),
                gettext('October'),
                gettext('November'),
                gettext('December'),
            ],
            datasets: [{
                label: gettext('Students'),
                backgroundColor: 'rgba(86, 224, 224, 0.5)',
                borderColor: 'rgb(86, 224, 224)',
                data: [0, 10, 5, 2, 20, 30, 45, 50, 60, 70, 80, 90]
            }, {
                label: gettext('Teachers'),
                backgroundColor: 'rgba(253, 174, 28, 0.5)',
                borderColor: 'rgb(253, 174, 28)',
                data: [20, 0, 15, 4, 6, 4, 60, 70, 80, 90, 100, 110],
            }, {
                label: gettext('Admins'),
                backgroundColor: 'rgba(203, 31, 255, 0.5)',
                borderColor: 'rgb(203, 31, 255)',
                data: [85, 30, 34, 20, 20, 55, 45, 50, 60, 70, 80, 90],
            }, {
                label: gettext('Stuffs'),
                backgroundColor: 'rgba(255, 19, 157, 0.5)',
                borderColor: 'rgb(255, 19, 157)',
                data: [45, 75, 70, 80, 20, 30, 90, 100, 110, 120, 130, 140],
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: true,
                }
            }
        }
    });

    // Enrollment Chart
    const enrollmentCtx = document.getElementById('enrollement').getContext('2d');
    const enrollmentChart = new Chart(enrollmentCtx, {
        type: 'bar',
        data: {
            labels: ['2021', '2022', '2023', '2024', '2025'],
            datasets: [{
                label: gettext('Comp.S'),
                backgroundColor: 'rgba(86, 224, 224, 0.5)',
                borderColor: 'rgb(86, 224, 224)',
                data: [0, 10, 5, 2, 20]
            }, {
                label: gettext('Architecture'),
                backgroundColor: 'rgba(253, 174, 28, 0.5)',
                borderColor: 'rgb(253, 174, 28)',
                data: [20, 0, 15, 4, 6],
            }, {
                label: gettext('Civil Eng'),
                backgroundColor: 'rgba(203, 31, 255, 0.5)',
                borderColor: 'rgb(203, 31, 255)',
                data: [85, 30, 34, 20, 20],
            }, {
                label: gettext('Accounting'),
                backgroundColor: 'rgba(255, 19, 157, 0.5)',
                borderColor: 'rgb(255, 19, 157)',
                data: [45, 75, 70, 80, 20],
            }, {
                label: gettext('Business M.'),
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                borderColor: 'rgb(0, 0, 0)',
                data: [15, 75, 45, 90, 60],
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: true,
                }
            }
        }
    });

    // Students Grade Chart
    const studentsGradeCtx = document.getElementById('students_grade').getContext('2d');
    const studentsGradeChart = new Chart(studentsGradeCtx, {
        type: 'bar',
        data: {
            labels: ['2021', '2022', '2023', '2024', '2025'],
            datasets: [{
                label: gettext("Comp sci."),
                backgroundColor: 'rgba(86, 224, 224, 0.5)',
                borderColor: 'rgb(86, 224, 224)',
                data: [0, 10, 5, 2, 20]
            }, {
                label: gettext("Civil eng."),
                backgroundColor: 'rgba(253, 174, 28, 0.5)',
                borderColor: 'rgb(253, 174, 28)',
                data: [20, 0, 15, 4, 6],
            }, {
                label: gettext("Architect."),
                backgroundColor: 'rgba(203, 31, 255, 0.5)',
                borderColor: 'rgb(203, 31, 255)',
                data: [85, 30, 34, 20, 20],
            }, {
                label: gettext("Economics"),
                backgroundColor: 'rgba(255, 19, 157, 0.5)',
                borderColor: 'rgb(255, 19, 157)',
                data: [45, 75, 70, 80, 20],
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: true,
                }
            }
        }
    });

    // Gender Chart
    const genderCtx = document.getElementById('gender').getContext('2d');
    const genderChart = new Chart(genderCtx, {
        type: 'pie',
        data: {
            labels: [gettext('Man'), gettext('Women')],
            datasets: [{
                label: gettext("Students Gender Dataset"),
                data: [malesCount, femalesCount],
                backgroundColor: ['rgb(255, 99, 132)', 'rgb(54, 162, 235)'],
                hoverOffset: 4
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: true,
                }
            }
        }
    });

    // Ethnicity Chart
    const ethnicityCtx = document.getElementById('ethnicity').getContext('2d');
    const ethnicityChart = new Chart(ethnicityCtx, {
        type: 'pie',
        data: {
            labels: [gettext('PHD'), gettext('Masters'), gettext('BSc degree')],
            datasets: [{
                label: gettext("Lecturer Qualifications Dataset"),
                data: [24, 30, 26],
                backgroundColor: ['rgb(255, 99, 132)', 'rgb(255, 193, 7)', 'rgb(54, 162, 235)'],
                hoverOffset: 4
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: true,
                }
            }
        }
    });

    // Language Chart
    const languageCtx = document.getElementById('language').getContext('2d');
    const languageChart = new Chart(languageCtx, {
        type: 'pie',
        data: {
            labels: [gettext('PHD'), gettext('Masters'), gettext('BSc degree')],
            datasets: [{
                label: gettext("Students level"),
                data: [14, 30, 56],
                backgroundColor: ['rgb(255, 99, 132)', 'rgb(255, 193, 7)', 'rgb(54, 162, 235)'],
                hoverOffset: 4
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: true,
                }
            }
        }
    });

    // Expand chart on click
    document.querySelectorAll('.fa-expand-alt').forEach(function (icon) {
        icon.addEventListener('click', function () {
            const parentCol = this.closest('.col-md-6');
            if (parentCol.classList.contains('expand')) {
                parentCol.classList.remove('expand');
            } else {
                document.querySelectorAll('.col-md-6.expand').forEach(function (col) {
                    col.classList.remove('expand');
                });
                parentCol.classList.add('expand');
            }
        });
    });
});