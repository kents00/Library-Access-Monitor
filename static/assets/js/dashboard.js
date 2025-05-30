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
  // Try to get course names from any existing chart data first
  const chartDataElement = document.getElementById('weekly_course_visits_data');
  if (chartDataElement && chartDataElement.value) {
    try {
      const existingData = JSON.parse(chartDataElement.value);
      if (existingData && typeof existingData === 'object' && Object.keys(existingData).length > 0) {
        // Create default data structure with the same course names but zero values
        const defaultData = {};
        Object.keys(existingData).forEach(courseName => {
          defaultData[courseName] = [0, 0, 0, 0, 0, 0, 0];
        });
        console.log('Using existing chart data structure with courses:', Object.keys(defaultData));
        return defaultData;
      }
    } catch (e) {
      console.warn('Could not parse existing chart data for default structure');
    }
  }

  // Try to fetch course names from the manage courses page if available
  const courseCards = document.querySelectorAll('[data-course-name]');
  if (courseCards.length > 0) {
    const defaultData = {};
    courseCards.forEach(card => {
      const courseName = card.dataset.courseName;
      if (courseName) {
        // Capitalize course name properly
        const properCourseName = courseName.split(' ')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
          .join(' ');
        defaultData[properCourseName] = [0, 0, 0, 0, 0, 0, 0];
      }
    });
    if (Object.keys(defaultData).length > 0) {
      console.log('Using course data from page elements:', Object.keys(defaultData));
      return defaultData;
    }
  }

  // Try to fetch from API if we're on dashboard and no cached data
  if (document.getElementById('visitorstat')) {
    fetchCoursesForDefaultData();
  }

  // Fallback to common course names if nothing else works
  console.log('Using fallback course data');
  return {
    'Information Technology': [0, 0, 0, 0, 0, 0, 0],
    'Marine Biology': [0, 0, 0, 0, 0, 0, 0],
    'Home Economics': [0, 0, 0, 0, 0, 0, 0],
    'Technology and Livelihood Education': [0, 0, 0, 0, 0, 0, 0]
  };
}

/**
 * Fetch courses from API to build default chart data structure
 */
function fetchCoursesForDefaultData() {
  fetch('/admin/manage_courses')
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to fetch courses');
      }
      return response.text(); // Get as text since it returns HTML
    })
    .then(html => {
      // Parse the HTML response to extract course data
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const courseCards = doc.querySelectorAll('[data-course-name]');

      if (courseCards.length > 0) {
        const defaultData = {};
        courseCards.forEach(card => {
          const courseName = card.dataset.courseName;
          if (courseName) {
            // Use course name as-is from the database
            defaultData[courseName] = [0, 0, 0, 0, 0, 0, 0];
          }
        });

        // Store the dynamic course data for future use
        window.dynamicCourseData = defaultData;
        console.log('Fetched courses from API:', Object.keys(defaultData));

        // Update chart if it exists
        if (visitorChart && Object.keys(defaultData).length > 0) {
          updateVisitorChart(defaultData);
        }

        // Update the hidden input with the new data
        const chartDataElement = document.getElementById('weekly_course_visits_data');
        if (chartDataElement) {
          chartDataElement.value = JSON.stringify(defaultData);
        }
      }
    })
    .catch(error => {
      console.warn('Could not fetch courses for default data:', error);
      // Try alternative API endpoint
      fetchCoursesFromAPI();
    });
}

/**
 * Alternative method to fetch courses directly from API
 */
function fetchCoursesFromAPI() {
  fetch('/api/admin/manage_courses')
    .then(response => response.json())
    .then(data => {
      if (data.success && data.courses) {
        const defaultData = {};
        data.courses.forEach(course => {
          defaultData[course.course_name] = [0, 0, 0, 0, 0, 0, 0];
        });

        window.dynamicCourseData = defaultData;
        console.log('Fetched courses from API endpoint:', Object.keys(defaultData));

        // Update chart if it exists
        if (visitorChart && Object.keys(defaultData).length > 0) {
          updateVisitorChart(defaultData);
        }
      }
    })
    .catch(error => {
      console.warn('Could not fetch courses from API endpoint:', error);
    });
}

/**
 * Get course data from various sources with fallback
 * @returns {Object} Course data structure
 */
function getCourseDataStructure() {
  // Check if we have cached dynamic course data
  if (window.dynamicCourseData && Object.keys(window.dynamicCourseData).length > 0) {
    return window.dynamicCourseData;
  }

  // Check chart data element
  const chartDataElement = document.getElementById('weekly_course_visits_data');
  if (chartDataElement && chartDataElement.value) {
    try {
      const data = JSON.parse(chartDataElement.value);
      if (data && typeof data === 'object' && Object.keys(data).length > 0) {
        return data;
      }
    } catch (e) {
      console.warn('Could not parse chart data element');
    }
  }

  // Return default structure
  return getDefaultChartData();
}

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
  // Try to get course names from any existing chart data first
  const chartDataElement = document.getElementById('weekly_course_visits_data');
  if (chartDataElement && chartDataElement.value) {
    try {
      const existingData = JSON.parse(chartDataElement.value);
      if (existingData && typeof existingData === 'object' && Object.keys(existingData).length > 0) {
        // Create default data structure with the same course names but zero values
        const defaultData = {};
        Object.keys(existingData).forEach(courseName => {
          defaultData[courseName] = [0, 0, 0, 0, 0, 0, 0];
        });
        console.log('Using existing chart data structure with courses:', Object.keys(defaultData));
        return defaultData;
      }
    } catch (e) {
      console.warn('Could not parse existing chart data for default structure');
    }
  }

  // Try to fetch course names from the manage courses page if available
  const courseCards = document.querySelectorAll('[data-course-name]');
  if (courseCards.length > 0) {
    const defaultData = {};
    courseCards.forEach(card => {
      const courseName = card.dataset.courseName;
      if (courseName) {
        // Capitalize course name properly
        const properCourseName = courseName.split(' ')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
          .join(' ');
        defaultData[properCourseName] = [0, 0, 0, 0, 0, 0, 0];
      }
    });
    if (Object.keys(defaultData).length > 0) {
      console.log('Using course data from page elements:', Object.keys(defaultData));
      return defaultData;
    }
  }

  // Try to fetch from API if we're on dashboard and no cached data
  if (document.getElementById('visitorstat')) {
    fetchCoursesForDefaultData();
  }

  // Fallback to common course names if nothing else works
  console.log('Using fallback course data');
  return {
    'Information Technology': [0, 0, 0, 0, 0, 0, 0],
    'Marine Biology': [0, 0, 0, 0, 0, 0, 0],
    'Home Economics': [0, 0, 0, 0, 0, 0, 0],
    'Technology and Livelihood Education': [0, 0, 0, 0, 0, 0, 0]
  };
}

/**
 * Fetch courses from API to build default chart data structure
 */
function fetchCoursesForDefaultData() {
  fetch('/admin/manage_courses')
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to fetch courses');
      }
      return response.text(); // Get as text since it returns HTML
    })
    .then(html => {
      // Parse the HTML response to extract course data
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const courseCards = doc.querySelectorAll('[data-course-name]');

      if (courseCards.length > 0) {
        const defaultData = {};
        courseCards.forEach(card => {
          const courseName = card.dataset.courseName;
          if (courseName) {
            // Use course name as-is from the database
            defaultData[courseName] = [0, 0, 0, 0, 0, 0, 0];
          }
        });

        // Store the dynamic course data for future use
        window.dynamicCourseData = defaultData;
        console.log('Fetched courses from API:', Object.keys(defaultData));

        // Update chart if it exists
        if (visitorChart && Object.keys(defaultData).length > 0) {
          updateVisitorChart(defaultData);
        }

        // Update the hidden input with the new data
        const chartDataElement = document.getElementById('weekly_course_visits_data');
        if (chartDataElement) {
          chartDataElement.value = JSON.stringify(defaultData);
        }
      }
    })
    .catch(error => {
      console.warn('Could not fetch courses for default data:', error);
      // Try alternative API endpoint
      fetchCoursesFromAPI();
    });
}

/**
 * Alternative method to fetch courses directly from API
 */
function fetchCoursesFromAPI() {
  fetch('/api/admin/manage_courses')
    .then(response => response.json())
    .then(data => {
      if (data.success && data.courses) {
        const defaultData = {};
        data.courses.forEach(course => {
          defaultData[course.course_name] = [0, 0, 0, 0, 0, 0, 0];
        });

        window.dynamicCourseData = defaultData;
        console.log('Fetched courses from API endpoint:', Object.keys(defaultData));

        // Update chart if it exists
        if (visitorChart && Object.keys(defaultData).length > 0) {
          updateVisitorChart(defaultData);
        }
      }
    })
    .catch(error => {
      console.warn('Could not fetch courses from API endpoint:', error);
    });
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

    // Get chart data using the safe method (no Jinja2 dependency)
    let chartData = getSafeChartData(chartDataElement.value);

    // If we don't have valid chart data, try to fetch it
    if (!chartData || Object.keys(chartData).length === 0) {
      console.log('No valid chart data found, fetching courses...');
      fetchCoursesForDefaultData();
      chartData = getDefaultChartData();
    }

    const chartContainer = document.getElementById('visitorstat');
    if (!chartContainer) {
      console.error('Chart container element not found');
      return;
    }

    console.log('Initializing chart with courses:', Object.keys(chartData));

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
      colors: ['#0d6efd', '#2ab57d', '#fd7e14', '#ff5c8e', '#6f42c1', '#e83e8c', '#20c997', '#fd7e14'],
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
        colors: ['#0d6efd', '#2ab57d', '#fd7e14', '#ff5c8e', '#6f42c1', '#e83e8c', '#20c997', '#fd7e14'],
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