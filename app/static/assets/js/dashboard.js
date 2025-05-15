$(function () {
  // =====================================
  // visitorstat
  // =====================================
  var weekly_course_visits = JSON.parse(document.getElementById('weekly_course_visits').textContent);
  var visitorstat = {
    series: [
      {
        name: "Information Technology",
        data: weekly_course_visits['Information Technology'],
      },
      {
        name: "Marine Biology",
        data: weekly_course_visits['Marine Biology'],
      },
      {
        name: "Home Economics",
        data: weekly_course_visits['Home Economics'],
      },
      {
        name: "Industrial Arts",
        data: weekly_course_visits['Industrial Arts'],
      },
    ],
    chart: {
      fontFamily: "Poppins,sans-serif",
      type: "bar",
      height: 360,
      offsetY: 10,
      toolbar: {
        show: false,
      },
    },
    grid: {
      show: true,
      strokeDashArray: 3,
      borderColor: "rgba(0,0,0,.1)",
    },
    colors: ["#1e88e5", "#21c1d6", "#ffb22b", "#ff5722"],
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: "50%",
        endingShape: "flat",
      },
    },
    dataLabels: {
      enabled: false,
    },
    stroke: {
      show: true,
      width: 5,
      colors: ["transparent"],
    },
    xaxis: {
      type: "category",
      categories: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
      axisTicks: {
        show: false,
      },
      axisBorder: {
        show: false,
      },
      labels: {
        style: {
          colors: "#a1aab2",
        },
      },
    },
    yaxis: {
      labels: {
        style: {
          colors: "#a1aab2",
        },
      },
    },
    fill: {
      opacity: 1,
      colors: ["var(--bs-primary)", "var(--bs-danger)", "var(--bs-warning)", "var(--bs-info)"],
    },
    tooltip: {
      theme: "dark",
    },
    legend: {
      show: false,
    },
    responsive: [
      {
        breakpoint: 767,
        options: {
          stroke: {
            show: false,
            width: 5,
            colors: ["transparent"],
          },
        },
      },
    ],
  };

  var chart_column_basic = new ApexCharts(
    document.querySelector("#visitorstat"),
    visitorstat
  );
  chart_column_basic.render();


  // Expose gradeColors to the global scope for use in the HTML template
  window.gradeColors = gradeColors;

  // =====================================
  // Earning
  // =====================================
  var earning = {
    chart: {
      id: "sparkline3",
      type: "area",
      height: 60,
      sparkline: {
        enabled: true,
      },
      group: "sparklines",
      fontFamily: "Plus Jakarta Sans', sans-serif",
      foreColor: "#adb0bb",
    },
    series: [
      {
        name: "Earnings",
        color: "#8763da",
        data: [25, 66, 20, 40, 12, 58, 20],
      },
    ],
    stroke: {
      curve: "smooth",
      width: 2,
    },
    fill: {
      colors: ["#f3feff"],
      type: "solid",
      opacity: 0.05,
    },

    markers: {
      size: 0,
    },
    tooltip: {
      theme: "dark",
      fixed: {
        enabled: true,
        position: "right",
      },
      x: {
        show: false,
      },
    },
  };
  new ApexCharts(document.querySelector("#earning"), earning).render();
})

document.getElementById('searchInput').addEventListener('keyup', function () {
  var input = document.getElementById('searchInput').value.toLowerCase();
  var rows = document.getElementById('studentTable').getElementsByTagName('tr');
  var noUsersFound = document.getElementById('noUsersFound');
  var matchFound = false;

  for (var i = 1; i < rows.length; i++) {
    var cells = rows[i].getElementsByTagName('td');
    var match = false;

    for (var j = 0; j < cells.length; j++) {
      if (cells[j].innerText.toLowerCase().includes(input)) {
        match = true;
        break;
      }
    }

    if (match) {
      rows[i].style.display = '';
      matchFound = true;
    } else {
      rows[i].style.display = 'none';
    }
  }

  if (!matchFound) {
    noUsersFound.style.display = '';
  } else {
    noUsersFound.style.display = 'none';
  }
});