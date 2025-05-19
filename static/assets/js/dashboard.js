/**
 * Dashboard charts and visualizations with dynamic updates from routes
 */

// Global variables to store chart and update timer
let visitorChart;
let updateTimer;
const UPDATE_INTERVAL = 30000; // Update every 30 seconds
const MAX_RETRIES = 3; // Maximum number of retry attempts for failed requests
let currentFilter = 'weekly'; // Track the current active filter

document.addEventListener('DOMContentLoaded', function () {
  // Initialize search functionality for student table
  initializeSearchFunctionality();

  // Initialize dashboard with initial data
  initDashboard();

  // Set up periodic updates
  startDynamicUpdates();

  // Setup dashboard filters to dynamically update data
  setupDashboardFilters();

  // Initialize the download link
  initializeDownloadLink();

  // Debug information
  if (window.debugToggleBtn && window.debugToggleBtn.classList.contains('active')) {
    console.log('Dashboard initialized with debugging enabled');
    logDashboardData();
  }
});

/**
 * Initialize search functionality for tables
 */
function initializeSearchFunctionality() {
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', function () {
      const searchTerm = this.value.toLowerCase();
      const rows = document.querySelectorAll('#studentTable tbody tr:not(#noUsersFound)');
      let visibleCount = 0;

      rows.forEach(function (row) {
        if (row.textContent.toLowerCase().includes(searchTerm)) {
          row.style.display = '';
          visibleCount++;
        } else {
          row.style.display = 'none';
        }
      });

      const noResultsRow = document.getElementById('noUsersFound');
      if (noResultsRow) {
        noResultsRow.style.display = visibleCount > 0 ? 'none' : '';
      }
    });
  }
}

/**
 * Initialize the dashboard with the first data load
 */
function initDashboard() {
  // Check if we're on the dashboard page first
  if (document.getElementById('visitorstat')) {
    // Initialize visitor statistics chart with initial data
    initVisitorStatsChart();

    // Load initial data from route
    fetchDashboardData('weekly'); // Default to weekly view
  }
}

/**
 * Set up UI elements to filter dashboard data
 */
function setupDashboardFilters() {
  // Check if filter buttons exist
  const filterItems = document.querySelectorAll('.dashboard-filter-item');

  if (filterItems.length > 0) {
    filterItems.forEach(item => {
      item.addEventListener('click', function (e) {
        e.preventDefault();

        // Remove active class from all items
        filterItems.forEach(btn => btn.classList.remove('active'));

        // Add active class to clicked item
        this.classList.add('active');

        // Get filter type
        const filterType = this.dataset.filter;
        currentFilter = filterType; // Update current filter state

        // Update filter display text
        updateFilterDisplay(filterType, this.textContent.trim());

        // Handle custom date range
        if (filterType === 'custom') {
          document.querySelector('.date-range-container').style.display = 'block';
        } else {
          document.querySelector('.date-range-container').style.display = 'none';

          // Show loading state
          showLoadingState();

          // Fetch data with the selected filter
          fetchDashboardData(filterType);
        }
      });
    });
  }

  // Custom date range button
  const customDateRangeBtn = document.getElementById('customDateRangeBtn');
  if (customDateRangeBtn) {
    customDateRangeBtn.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelector('.date-range-container').style.display = 'block';
    });
  }

  // Apply date range button
  const applyDateRangeBtn = document.getElementById('applyDateRange');
  if (applyDateRangeBtn) {
    applyDateRangeBtn.addEventListener('click', function () {
      const startDate = document.getElementById('startDate').value;
      const endDate = document.getElementById('endDate').value;

      if (startDate && endDate) {
        // Show loading state
        showLoadingState();

        // Update filter display with date range
        updateFilterDisplay('custom', `Custom (${formatDate(startDate)} to ${formatDate(endDate)})`);

        // Fetch data with custom date range
        fetchDashboardData('custom', { startDate, endDate });

        // Update download link with date parameters
        updateDownloadLink(startDate, endDate);
      } else {
        alert('Please select both start and end dates');
      }
    });
  }

  // Set initial dates for the date picker to current week
  const today = new Date();
  const startOfWeek = new Date(today);
  startOfWeek.setDate(today.getDate() - today.getDay()); // Start of current week (Sunday)

  const startDateInput = document.getElementById('startDate');
  const endDateInput = document.getElementById('endDate');

  if (startDateInput && endDateInput) {
    startDateInput.valueAsDate = startOfWeek;
    endDateInput.valueAsDate = today;
  }

  // Set initial active filter and display text
  updateFilterDisplay('weekly', 'Weekly');
}

/**
 * Update the filter display text
 * @param {string} filterType - Type of filter (weekly, monthly, yearly, custom)
 * @param {string} displayText - Text to display for the filter
 */
function updateFilterDisplay(filterType, displayText) {
  const filterDisplayElement = document.getElementById('activeFilterName');
  if (filterDisplayElement) {
    filterDisplayElement.textContent = displayText;
  }

  // Update the current filter indicator
  const filterDisplay = document.getElementById('currentFilterDisplay');
  if (filterDisplay) {
    // Change the background color based on the filter type
    filterDisplay.className = 'badge p-2';

    switch (filterType) {
      case 'weekly':
        filterDisplay.classList.add('bg-light-primary', 'text-primary');
        break;
      case 'monthly':
        filterDisplay.classList.add('bg-light-success', 'text-success');
        break;
      case 'yearly':
        filterDisplay.classList.add('bg-light-warning', 'text-warning');
        break;
      case 'custom':
        filterDisplay.classList.add('bg-light-info', 'text-info');
        break;
    }
  }
}

/**
 * Format date for display
 * @param {string} dateString - Date in YYYY-MM-DD format
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Update the download link with date parameters
 * @param {string} startDate - Start date in YYYY-MM-DD format
 * @param {string} endDate - End date in YYYY-MM-DD format
 * @param {string} graphType - Type of graph (weekly, monthly, summary)
 */
function updateDownloadLink(startDate, endDate, graphType = 'weekly') {
  const downloadLink = document.getElementById('downloadGraphLink');
  if (!downloadLink) return;

  try {
    const baseUrl = downloadLink.href.split('?')[0];
    const chartDataElement = document.getElementById('weekly_course_visits_data');

    if (!chartDataElement) {
      console.error('Chart data element not found');
      return;
    }

    // Get chart data safely
    let chartData = getSafeChartData(chartDataElement.value);

    // Check if we got valid data
    if (!chartData || Object.keys(chartData).length === 0) {
      console.error('No valid chart data available');
      return;
    }

    const jsonString = JSON.stringify(chartData);

    // Check if URL will be too long (browsers typically have a limit around 2000 chars)
    if (jsonString.length > 1500) {
      // For long data, change to a click handler that will use AJAX instead
      downloadLink.href = "#";
      downloadLink.onclick = function (e) {
        e.preventDefault();
        downloadGraphWithAjax(chartData, startDate, endDate, graphType);
        return false;
      };
    } else {
      // For shorter data, use URL parameters
      downloadLink.href = `${baseUrl}?weekly_course_visits=${encodeURIComponent(jsonString)}&start_date=${startDate}&end_date=${endDate}&type=${graphType}`;
      downloadLink.onclick = null;
    }
  } catch (e) {
    console.error('Error preparing download link:', e);
    // Set fallback URL without data parameter
    if (downloadLink) {
      downloadLink.href = `/download_graph?start_date=${startDate}&end_date=${endDate}&type=${graphType}`;
    }
  }
}

/**
 * Get safe chart data, handling various formats and errors
 * @param {string} dataValue - JSON string or raw data
 * @returns {Object} Parsed chart data object or default empty data
 */
function getSafeChartData(dataValue) {
  if (!dataValue) return getDefaultChartData();

  // Default chart data in case parsing fails
  let chartData = null;

  try {
    // Check if it's already an object (not a string)
    if (typeof dataValue === 'object') {
      return dataValue;
    }

    // First, try to parse the raw value
    chartData = JSON.parse(dataValue);

    // Log success
    console.log('Successfully parsed chart data');
    return chartData;
  }
  catch (parseError) {
    console.warn('Error parsing chart data:', parseError);
    console.log('Raw data:', dataValue);

    // Try to detect HTML encoding issues
    if (dataValue.includes('&quot;')) {
      try {
        // Try replacing HTML entities and parse again
        const decodedValue = dataValue
          .replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'")
          .replace(/&amp;/g, '&');
        chartData = JSON.parse(decodedValue);
        console.log('Successfully parsed chart data after HTML decoding');
        return chartData;
      } catch (e) {
        console.error('Failed to parse even after HTML decoding:', e);
      }
    }

    // If all else fails, return default data
    return getDefaultChartData();
  }
}

/**
 * Get default chart data structure
 * @returns {Object} Default chart data structure
 */
function getDefaultChartData() {
  return {
    'Information Technology': [0, 0, 0, 0, 0, 0, 0],
    'Marine Biology': [0, 0, 0, 0, 0, 0, 0],
    'Home Economics and Industrial Arts': [0, 0, 0, 0, 0, 0, 0],
    'Technology and Livelihood Education': [0, 0, 0, 0, 0, 0, 0]
  };
}

/**
 * Initialize the download link with proper parameters
 */
function initializeDownloadLink() {
  try {
    const downloadLink = document.getElementById('downloadGraphLink');
    if (!downloadLink) {
      console.warn('Download link element not found');
      return;
    }

    const startDate = document.getElementById('startDate')?.value;
    const endDate = document.getElementById('endDate')?.value;

    if (startDate && endDate) {
      updateDownloadLink(startDate, endDate);
    } else {
      // Use current week as default date range for download
      const today = new Date();
      const startOfWeek = new Date(today);
      startOfWeek.setDate(today.getDate() - today.getDay()); // Start of current week (Sunday)

      const formattedStart = startOfWeek.toISOString().split('T')[0];
      const formattedEnd = today.toISOString().split('T')[0];

      updateDownloadLink(formattedStart, formattedEnd);
    }
  } catch (e) {
    console.error('Error initializing download link:', e);
  }
}

/**
 * Download graph using AJAX for large datasets
 * @param {Object} chartData - The chart data object
 * @param {string} startDate - Start date in YYYY-MM-DD format
 * @param {string} endDate - End date in YYYY-MM-DD format
 * @param {string} graphType - Type of graph (weekly, monthly, summary)
 */
function downloadGraphWithAjax(chartData, startDate, endDate, graphType = 'weekly') {
  // Create a form element
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/download_graph';
  form.style.display = 'none';

  // Add the chart data
  const dataInput = document.createElement('input');
  dataInput.type = 'hidden';
  dataInput.name = 'weekly_course_visits';
  dataInput.value = JSON.stringify(chartData);
  form.appendChild(dataInput);

  // Add date parameters if available
  if (startDate) {
    const startInput = document.createElement('input');
    startInput.type = 'hidden';
    startInput.name = 'start_date';
    startInput.value = startDate;
    form.appendChild(startInput);
  }

  if (endDate) {
    const endInput = document.createElement('input');
    endInput.type = 'hidden';
    endInput.name = 'end_date';
    endInput.value = endDate;
    form.appendChild(endInput);
  }

  // Add graph type parameter
  const typeInput = document.createElement('input');
  typeInput.type = 'hidden';
  typeInput.name = 'type';
  typeInput.value = graphType;
  form.appendChild(typeInput);

  // Add the form to the document and submit it
  document.body.appendChild(form);
  form.submit();
}

/**
 * Show loading indicators on dashboard widgets
 */
function showLoadingState() {
  // Add loading class to chart containers
  const containers = document.querySelectorAll('.chart-container');
  containers.forEach(container => {
    container.classList.add('loading');
    const loader = document.createElement('div');
    loader.className = 'chart-loader';
    loader.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';

    // Only append if not already there
    if (!container.querySelector('.chart-loader')) {
      container.appendChild(loader);
    }
  });

  // Add loading indicator to global refresh indicator
  const loadingIndicator = $('.auto-refresh-indicator .badge');
  if (loadingIndicator.length) {
    loadingIndicator.addClass('pulsing').html('<i class="ti ti-loader ti-spin me-1"></i> Refreshing data...');
  }
}

/**
 * Hide loading indicators on dashboard widgets
 */
function hideLoadingState() {
  // Remove loading class from chart containers
  const containers = document.querySelectorAll('.chart-container');
  containers.forEach(container => {
    container.classList.remove('loading');
    const loader = container.querySelector('.chart-loader');
    if (loader) {
      container.removeChild(loader);
    }
  });

  // Reset the loading indicator
  const loadingIndicator = $('.auto-refresh-indicator .badge');
  if (loadingIndicator.length) {
    loadingIndicator.removeClass('pulsing').html('<i class="ti ti-refresh me-1"></i> Auto-refresh active');
  }
}

/**
 * Start periodic updates for dynamic data
 */
function startDynamicUpdates() {
  // Check if we're on the dashboard page first
  if (!document.querySelector('.container-fluid')) {
    console.log('Not on dashboard page, skipping dynamic updates');
    return;
  }

  // Clear any existing timers
  if (updateTimer) {
    clearInterval(updateTimer);
  }

  // Set up periodic data refresh
  updateTimer = setInterval(() => {
    // Get current active filter
    const activeFilter = document.querySelector('.dashboard-filter-item.active');
    const filterType = activeFilter ? activeFilter.dataset.filter : currentFilter;

    // Only fetch data if not on custom view (to avoid overriding user-selected dates)
    if (filterType !== 'custom' || !document.querySelector('.date-range-container').style.display === 'block') {
      fetchDashboardData(filterType);
    }
  }, UPDATE_INTERVAL);

  // Add visual indicator that auto-refresh is active
  const refreshIndicator = document.createElement('div');
  refreshIndicator.className = 'auto-refresh-indicator';
  refreshIndicator.innerHTML = '<div class="badge bg-info text-white"><i class="ti ti-refresh me-1"></i> Auto-refresh active</div>';

  // Add to the body for bottom-right overlay positioning
  if (!document.querySelector('.auto-refresh-indicator')) {
    document.body.appendChild(refreshIndicator);
  }
}

/**
 * Fetch updated dashboard data via AJAX with filter options
 * @param {string} filterType - Type of filter (weekly, monthly, yearly, custom)
 * @param {Object} customParams - Custom parameters for the request
 * @param {number} retryCount - Current retry attempt (for internal use)
 */
function fetchDashboardData(filterType = 'weekly', customParams = {}, retryCount = 0) {
  // Build URL for API request
  let url = '/api/admin';
  let requestData = { filter: filterType };

  // Add any custom parameters
  if (customParams && Object.keys(customParams).length > 0) {
    requestData = { ...requestData, ...customParams };
  }

  // Store the current filter for future use
  currentFilter = filterType;

  // Update UI to show which filter is active
  const filterItems = document.querySelectorAll('.dashboard-filter-item');
  filterItems.forEach(item => {
    if (item.dataset.filter === filterType) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  $.ajax({
    url: url,
    method: 'GET',
    data: requestData,
    dataType: 'json',
    contentType: "application/json; charset=utf-8",
    timeout: 30000, // 30 seconds timeout
    beforeSend: function (xhr) {
      // Show loading indicators
      showLoadingState();

      // Add headers to prevent caching issues
      xhr.setRequestHeader("Cache-Control", "no-cache, no-store, must-revalidate");
      xhr.setRequestHeader("Pragma", "no-cache");
      xhr.setRequestHeader("Expires", "0");

      // Show filter type in console for debugging
      console.log(`Fetching dashboard data with filter: ${filterType}`, requestData);
    },
    success: function (data) {
      // Reset retry counter on success
      retryCount = 0;

      // Check if data is valid
      if (!data) {
        console.error('Received empty data from API');
        showError('Error loading dashboard data: Empty response');
        return;
      }

      // Update the dashboard with new data
      updateDashboardWithNewData(data);

      // If in debug mode, log the new data
      if (window.debugToggleBtn && window.debugToggleBtn.classList.contains('active')) {
        console.log(`New dashboard data received (${filterType}):`, data);
      }

      // Update timestamp to show real-time update
      updateDataTimestamp(true);

      // If this is a custom date range request, keep the date range picker open
      if (filterType === 'custom') {
        document.querySelector('.date-range-container').style.display = 'block';
      }
    },
    error: function (xhr, status, error) {
      console.error('Error fetching dashboard data:', error, 'Status:', status);

      if (status === 'parsererror') {
        console.error('JSON parsing error. Raw response:', xhr.responseText);

        // If the response is empty, show a specific message
        if (!xhr.responseText || xhr.responseText.trim() === '') {
          showError('Server returned an empty response. Please check if the backend API is running.');
        } else {
          showError('Error parsing server response. Please check console for details.');
        }
      }
      else if (status === 'timeout') {
        showError('Server request timed out. The server might be under heavy load.');
      }
      else if (status === 'error' && retryCount < MAX_RETRIES) {
        // Retry the request with exponential backoff
        const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
        console.log(`Retrying in ${delay / 1000} seconds... (Attempt ${retryCount + 1}/${MAX_RETRIES})`);

        setTimeout(() => {
          fetchDashboardData(filterType, customParams, retryCount + 1);
        }, delay);
        return;
      }
      else {
        showError(`Failed to load dashboard data: ${error || 'Unknown error'}`);
      }

      // If we have response text, try to diagnose the issue
      if (xhr.responseText) {
        try {
          const errorData = JSON.parse(xhr.responseText);
          console.error('API Error details:', errorData);
        } catch (e) {
          console.error('API Response (not JSON):', xhr.responseText);
          console.error('Parse error:', e);
        }
      }

      // Show error in debug console
      if (window.debugToggleBtn && window.debugToggleBtn.classList.contains('active')) {
        console.error('AJAX Error details:', xhr);
      }
    },
    complete: function () {
      // Hide loading indicators
      hideLoadingState();
    }
  });
}

/**
 * Display an error message on the dashboard
 */
function showError(message) {
  // Create error toast notification
  const errorToast = `
    <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 11">
      <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-header bg-danger text-white">
          <strong class="me-auto">Error</strong>
          <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
          ${message}
        </div>
      </div>
    </div>
  `;

  // Remove any existing error toasts
  const existingToasts = document.querySelectorAll('.toast');
  existingToasts.forEach(toast => toast.parentNode.removeChild(toast));

  // Add the error toast to the page
  const toastContainer = document.createElement('div');
  toastContainer.innerHTML = errorToast;
  document.body.appendChild(toastContainer);

  // Auto-hide after 5 seconds
  setTimeout(() => {
    const toast = document.querySelector('.toast');
    if (toast) {
      toast.classList.remove('show');
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 500);
    }
  }, 5000);
}

/**
 * Update all dashboard components with new data
 */
function updateDashboardWithNewData(data) {
  if (!data) return;

  // Update visitor statistics chart
  if (data.weekly_course_visits) {
    updateVisitorChart(data.weekly_course_visits);
  }

  // Update the recently logged-in students table
  if (data.logged_in_users) {
    updateLoggedInUsersTable(data.logged_in_users);
  }

  // Update place of residence data
  if (data.top_weekly_places) {
    updateTopPlaces(data.top_weekly_places,
      data.top_weekly_place_visits_icon_class || 'ti-arrow-up-left text-success',
      data.top_weekly_place_visits_bg_class || 'bg-light-success');
  }

  // Update total logins
  if (typeof data.total_logins_month !== 'undefined') {
    updateTotalLogins(
      data.total_logins_month,
      data.login_percentage_increase || 0,
      data.login_icon_class || 'ti-arrow-up-left text-success',
      data.login_bg_class || 'bg-light-success'
    );
  }

  // Update total visitors card
  if (typeof data.total_visitors !== 'undefined') {
    updateTotalVisitors(data.total_visitors);
  }

  // Update data timestamp to show when data was last updated
  updateDataTimestamp();
}

/**
 * Update the visitor statistics chart with new data
 */
function updateVisitorChart(chartData) {
  if (!chartData) {
    console.error('No chart data provided for update');
    return;
  }

  try {
    // Convert chart data to the format needed by ApexCharts
    const series = Object.entries(chartData).map(([name, data]) => ({
      name: name,
      data: data
    }));

    // If chart already exists, just update the series
    if (visitorChart) {
      visitorChart.updateSeries(series);
    } else {
      // If chart doesn't exist yet, initialize it
      initVisitorStatsChart();
    }
  } catch (err) {
    console.error('Error updating visitor chart:', err);

    // Show error message in chart container
    if (document.getElementById('visitorstat')) {
      document.getElementById('visitorstat').innerHTML =
        '<div class="alert alert-danger">Error updating chart. Check console for details.</div>';
    }
  }
}

/**
 * Initialize visitor statistics chart
 */
function initVisitorStatsChart() {
  try {
    const chartDataElement = document.getElementById('weekly_course_visits_data');
    if (!chartDataElement) {
      console.error('Chart data element not found');
      return;
    }

    // Add debug logging to see the raw value
    console.log('Raw chart data:', chartDataElement.value);

    let chartData;
    try {
      // Ensure the value is a valid JSON string
      const jsonData = chartDataElement.value.trim();

      // Log the first few characters to help diagnose the issue
      console.log('First 10 chars of JSON:', jsonData.substring(0, 10));

      chartData = JSON.parse(jsonData);
    } catch (e) {
      console.error('Error parsing chart data:', e);

      // Set default chart data even if parsing fails
      chartData = {
        'Information Technology': [0, 0, 0, 0, 0, 0, 0],
        'Marine Biology': [0, 0, 0, 0, 0, 0, 0],
        'Home Economics and Industrial Arts': [0, 0, 0, 0, 0, 0, 0],
        'Technology and Livelihood Education': [0, 0, 0, 0, 0, 0, 0]
      };
    }

    const chartContainer = document.getElementById('visitorstat');
    if (!chartContainer) {
      console.error('Chart container element not found');
      return;
    }

    // Transform data for ApexCharts
    const series = Object.entries(chartData).map(([name, data]) => ({
      name: name,
      data: data
    }));

    // Initialize ApexCharts with responsive options
    const options = {
      series: series,
      chart: {
        height: 350,
        type: 'line',
        animations: {
          enabled: true,
          easing: 'easeinout',
          speed: 800,
          dynamicAnimation: {
            enabled: true,
            speed: 350
          }
        },
        toolbar: {
          show: false, // Disable toolbar completely
        },
        zoom: {
          enabled: false // Disable zoom since toolbar is hidden
        }
      },
      colors: ['#0d6efd', '#2ab57d', '#fd7e14', '#ff5c8e'],
      dataLabels: {
        enabled: false,
      },
      stroke: {
        curve: 'smooth',
        width: 3,
      },
      grid: {
        borderColor: 'rgba(0,0,0,0.1)',
        strokeDashArray: 3,
        xaxis: {
          lines: {
            show: false
          }
        }
      },
      markers: {
        size: 3,
        colors: ['#0d6efd', '#2ab57d', '#fd7e14', '#ff5c8e'],
        strokeColors: '#ffffff',
        strokeWidth: 2,
        hover: {
          size: 7,
        }
      },
      xaxis: {
        categories: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        title: {
          text: 'Day of Week'
        }
      },
      yaxis: {
        title: {
          text: 'Number of Visitors'
        },
        min: 0,
        forceNiceScale: true
      },
      legend: {
        position: 'top',
        horizontalAlign: 'right',
        onItemClick: {
          toggleDataSeries: true
        }
      },
      tooltip: {
        shared: true,
        intersect: false,
        y: {
          formatter: function (y) {
            if (typeof y !== "undefined") {
              return y.toFixed(0) + " visits";
            }
            return y;
          }
        }
      },
      responsive: [
        {
          breakpoint: 600,
          options: {
            legend: {
              position: 'bottom',
              horizontalAlign: 'center'
            }
          }
        }
      ]
    };

    // Store the chart instance in the global variable
    visitorChart = new ApexCharts(chartContainer, options);
    visitorChart.render();
  } catch (err) {
    console.error('Error rendering visitor stats chart:', err);
    if (document.getElementById('visitorstat')) {
      document.getElementById('visitorstat').innerHTML =
        '<div class="alert alert-danger">Error rendering chart. Check console for details.</div>';
    }
  }
}

/**
 * Update the recently logged-in users table with new data
 */
function updateLoggedInUsersTable(users) {
  if (!users || !Array.isArray(users)) {
    console.error('Invalid users data provided for update');
    return;
  }

  try {
    const tableBody = $('#studentTable tbody');
    if (!tableBody.length) {
      console.error('Student table body not found');
      return;
    }

    // Clear existing rows except the "No users found" row
    tableBody.find('tr:not(#noUsersFound)').remove();

    if (users.length === 0) {
      // Show the "No users found" row
      $('#noUsersFound').show();
    } else {
      // Hide the "No users found" row
      $('#noUsersFound').hide();

      // Add new rows for each user
      users.forEach(userData => {
        const student = userData.student;
        if (!student) return;

        const loginTime = userData.login_time ? new Date(userData.login_time) : null;
        const formattedTime = loginTime ?
          loginTime.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true }) :
          'N/A';

        const courseName = student.course ? student.course.course_name : 'N/A';
        const imagePath = student.image ?
          `/static/uploads/${student.image}` :
          '/static/uploads/default.png';

        // Create and append new row with animation
        const newRow = $(`
          <tr class="fade-in">
            <td>
              <div class="d-flex align-items-center">
                <div class="me-4">
                  <img src="${imagePath}" width="50" class="rounded-circle" alt="" />
                </div>
                <div>
                  <h6 class="mb-1 fw-bolder">${student.first_name} ${student.last_name}</h6>
                  <p class="fs-3 mb-0">Student</p>
                </div>
              </div>
            </td>
            <td>
              <p class="fs-3 fw-normal mb-0">${student.id}</p>
            </td>
            <td>
              <p class="fs-3 fw-normal mb-0">${courseName}</p>
            </td>
            <td>
              <span class="badge bg-light-success rounded-pill text-success px-3 py-2 fs-3">${formattedTime}</span>
            </td>
          </tr>
        `);

        tableBody.append(newRow);
      });
    }

    // Re-apply search filtering if there's a search term
    const searchTerm = $('#searchInput').val();
    if (searchTerm && searchTerm.length > 0) {
      $('#searchInput').trigger('input');
    }
  } catch (err) {
    console.error('Error updating users table:', err);
  }
}

/**
 * Update the top place of residence widget
 */
function updateTopPlaces(topPlaces, iconClass, bgClass) {
  if (!topPlaces || !Array.isArray(topPlaces)) {
    return;
  }

  try {
    const placeWidget = $('.card-title:contains("Visits by Place of Residence")').closest('.card-body');
    if (!placeWidget.length) return;

    // Get the container with the place data
    const placeContainer = placeWidget.find('.col-7');
    if (!placeContainer.length) return;

    if (topPlaces.length === 0) {
      placeContainer.html('<p class="text-center">No Data Available</p>');
      return;
    }

    // Update the place data
    let html = `
      <h4 class="fw-semibold mb-3">${topPlaces[0].municipality}</h4>
      <div class="d-flex align-items-center mb-2">
        <span class="me-1 rounded-circle ${bgClass} round-20 d-flex align-items-center justify-content-center">
          <i class="ti ${iconClass}"></i>
        </span>
        <p class="text-dark me-1 fs-3 mb-0">+${topPlaces[0].visits}%</p>
        <p class="fs-3 mb-0">this month</p>
      </div>
      <div class="d-flex align-items-center">
        <div class="me-3">
          <span class="round-8 bg-primary rounded-circle me-2 d-inline-block"></span>
          <span class="fs-2">${topPlaces[0].municipality}</span>
        </div>
    `;

    if (topPlaces.length > 1) {
      html += `
        <div>
          <span class="round-8 bg-danger rounded-circle me-2 d-inline-block"></span>
          <span class="fs-2">${topPlaces[1].municipality}</span>
        </div>
      `;
    }

    html += '</div>';
    placeContainer.html(html);
  } catch (err) {
    console.error('Error updating top places widget:', err);
  }
}

/**
 * Update the total logins widget
 */
function updateTotalLogins(totalLogins, percentageIncrease, iconClass, bgClass) {
  try {
    const loginWidget = $('.card-title:contains("Total Log-in Library")').closest('.card-body');
    if (!loginWidget.length) return;

    // Update the values
    loginWidget.find('h4.fw-semibold').text(totalLogins);

    // Update the percentage and icon
    const percentageContainer = loginWidget.find('.d-flex.align-items-center.pb-1');
    if (percentageContainer.length) {
      percentageContainer.html(`
        <span class="me-2 rounded-circle ${bgClass} round-20 d-flex align-items-center justify-content-center">
          <i class="ti ${iconClass}"></i>
        </span>
        <p class="text-dark me-1 fs-3 mb-0">${percentageIncrease}%</p>
        <p class="fs-3 mb-0">this month</p>
      `);
    }
  } catch (err) {
    console.error('Error updating total logins widget:', err);
  }
}

/**
 * Update total visitors card with new data
 */
function updateTotalVisitors(totalVisitors) {
  try {
    const visitorsWidget = $('.card-title:contains("Total Visitors")').closest('.card-body');
    if (!visitorsWidget.length) return;

    // Update total visitors count
    visitorsWidget.find('h4.fw-semibold').text(totalVisitors);
  } catch (err) {
    console.error('Error updating total visitors widget:', err);
  }
}

/**
 * Update timestamp showing when data was last refreshed
 * @param {boolean} success - Whether the update was successful
 */
function updateDataTimestamp(success = true) {
  try {
    // Create or update the timestamp element
    let timestampElement = document.getElementById('data-last-updated');
    if (!timestampElement) {
      timestampElement = document.createElement('div');
      timestampElement.id = 'data-last-updated';
      timestampElement.className = 'data-timestamp text-muted d-flex align-items-center justify-content-end mt-2';

      // Add the timestamp element to the page
      const container = document.querySelector('.container-fluid');
      if (container) {
        container.appendChild(timestampElement);
      }
    }

    // Update the timestamp text with server time if available
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    const dateString = now.toLocaleDateString();

    if (success) {
      timestampElement.innerHTML = `
        <span class="badge bg-success me-2"></span>
        Data updated at ${timeString} on ${dateString}
        <button id="manualRefreshBtn" class="btn btn-sm btn-link ms-2" title="Refresh now">
          <i class="ti ti-refresh"></i>
        </button>
      `;

      // Add click event to the manual refresh button
      const refreshBtn = document.getElementById('manualRefreshBtn');
      if (refreshBtn) {
        refreshBtn.addEventListener('click', function () {
          // Get current active filter
          const activeFilter = document.querySelector('.dashboard-filter-item.active');
          const filterType = activeFilter ? activeFilter.dataset.filter : 'weekly';

          fetchDashboardData(filterType);
        });
      }
    } else {
      timestampElement.innerHTML = `
        <span class="badge bg-danger me-2"></span>
        Update failed at ${timeString}
        <button id="manualRefreshBtn" class="btn btn-sm btn-link ms-2" title="Try again">
          <i class="ti ti-refresh"></i>
        </button>
      `;
    }
  } catch (err) {
    console.error('Error updating data timestamp:', err);
  }
}

/**
 * Debug function to log dashboard data
 */
function logDashboardData() {
  try {
    const elements = {
      weekly_course_visits: document.getElementById('weekly_course_visits_data'),
      logged_in_users: document.querySelectorAll('#studentTable tbody tr:not(#noUsersFound)'),
      top_weekly_places: document.querySelector('.card-title:contains("Visits by Place of Residence")'),
      total_logins: document.querySelector('.card-title:contains("Total Log-in Library")')
    };

    console.group('Dashboard Data Debug');
    for (const [key, element] of Object.entries(elements)) {
      if (element) {
        if (key === 'weekly_course_visits' && element.value) {
          try {
            console.log(key + ':', JSON.parse(element.value));
          } catch (e) {
            console.error('Error parsing JSON for ' + key + ':', element.value);
          }
        } else if (element.length) {
          console.log(key + ':', element.length + ' items found');
        } else {
          console.log(key + ':', 'Element found');
        }
      } else {
        console.warn(key + ':', 'Element not found');
      }
    }
    console.groupEnd();
  } catch (err) {
    console.error('Error in debug logging:', err);
  }
}

// Add styles for the refresh indicator and animations
$(document).ready(function () {
  $('<style>')
    .prop('type', 'text/css')
    .html(`
      .auto-refresh-indicator {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1050;
        pointer-events: none; /* Make it non-clickable */
        transition: all 0.3s ease;
      }
      .auto-refresh-indicator .badge {
        padding: 8px 12px;
        border-radius: 6px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        font-size: 12px;
        opacity: 0.9;
        white-space: nowrap;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: bold;
      }
      .auto-refresh-indicator:hover {
        transform: translateY(-3px);
      }
      .pulsing {
        animation: pulse 1.5s infinite;
      }
      @keyframes pulse {
        0% { opacity: 0.9; }
        50% { opacity: 0.5; }
        100% { opacity: 0.9; }
      }
      .fade-in {
        animation: fadeIn 0.5s;
      }
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .chart-container.loading {
        position: relative;
        min-height: 150px;
      }
      .chart-loader {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: rgba(255, 255, 255, 0.7);
        z-index: 10;
      }
      .container-fluid {
        padding-top: 24px !important;
      }
      #main-wrapper[data-layout="vertical"][data-header-position="fixed"] .body-wrapper > .container-fluid {
        padding-top: calc(56px + 24px) !important; /* $header-height + padding */
      }
      @media (max-width: 767.98px) {
        .container-fluid {
          padding: 16px !important;
          padding-top: 24px !important;
        }
        #main-wrapper[data-layout="vertical"][data-header-position="fixed"] .body-wrapper > .container-fluid {
          padding-top: calc(56px + 16px) !important;
        }
      }
    `)
    .appendTo('head');
});