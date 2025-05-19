/**
 * Debug Panel for monitoring AJAX requests and responses
 */
(function() {
  // Debug state
  let isDebugActive = false;
  let requestLog = [];
  const MAX_LOG_ENTRIES = 50;

  // Initialize debug panel when document is ready
  document.addEventListener('DOMContentLoaded', function() {
    createDebugPanel();
    setupAjaxInterceptors();

    // Toggle debug panel with the button
    document.getElementById('debugToggleBtn').addEventListener('click', function() {
      toggleDebugPanel();
    });

    // Clear log button
    document.getElementById('debugClearBtn').addEventListener('click', function() {
      clearDebugLog();
    });
  });

  function createDebugPanel() {
    // Create debug panel HTML
    const debugPanel = document.createElement('div');
    debugPanel.id = 'debugPanel';
    debugPanel.className = 'debug-panel';
    debugPanel.innerHTML = `
      <div class="debug-header">
        <h5>Debug Console</h5>
        <div class="debug-controls">
          <button id="debugClearBtn" class="btn btn-sm btn-light">Clear</button>
          <button id="debugCloseBtn" class="btn btn-sm btn-light">×</button>
        </div>
      </div>
      <div class="debug-content">
        <div id="debugLog" class="debug-log"></div>
      </div>
    `;
    document.body.appendChild(debugPanel);

    // Close button event
    document.getElementById('debugCloseBtn').addEventListener('click', function() {
      toggleDebugPanel(false);
    });
  }

  function toggleDebugPanel(forceState) {
    isDebugActive = forceState !== undefined ? forceState : !isDebugActive;

    const debugPanel = document.getElementById('debugPanel');
    const debugToggle = document.getElementById('debugToggleBtn');

    if (isDebugActive) {
      debugPanel.classList.add('active');
      debugToggle.classList.add('active');
      debugToggle.querySelector('i').classList.add('text-danger');
    } else {
      debugPanel.classList.remove('active');
      debugToggle.classList.remove('active');
      debugToggle.querySelector('i').classList.remove('text-danger');
    }

    // Store preference in localStorage
    localStorage.setItem('debugPanelActive', isDebugActive);
  }

  function setupAjaxInterceptors() {
    // Intercept fetch requests
    const originalFetch = window.fetch;
    window.fetch = async function(url, options) {
      if (!isDebugActive) return originalFetch(url, options);

      const requestId = Math.random().toString(36).substring(2);
      const requestData = {
        url,
        method: options?.method || 'GET',
        headers: options?.headers || {},
        body: options?.body || null,
        timestamp: new Date()
      };

      logRequest(requestId, requestData);

      try {
        const response = await originalFetch(url, options);
        const clonedResponse = response.clone();

        clonedResponse.text().then(body => {
          try {
            const jsonBody = JSON.parse(body);
            logResponse(requestId, {
              status: response.status,
              statusText: response.statusText,
              headers: Object.fromEntries([...response.headers.entries()]),
              body: jsonBody,
              timestamp: new Date()
            });
          } catch (e) {
            // Not JSON, log as text
            logResponse(requestId, {
              status: response.status,
              statusText: response.statusText,
              headers: Object.fromEntries([...response.headers.entries()]),
              body: body.substring(0, 500) + (body.length > 500 ? '...' : ''),
              timestamp: new Date()
            });
          }
        });

        return response;
      } catch (error) {
        logError(requestId, error);
        throw error;
      }
    };

    // Intercept XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url) {
      this._debugRequestId = Math.random().toString(36).substring(2);
      this._debugUrl = url;
      this._debugMethod = method;
      return originalOpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function(body) {
      if (isDebugActive && this._debugRequestId) {
        logRequest(this._debugRequestId, {
          url: this._debugUrl,
          method: this._debugMethod,
          body: body || null,
          timestamp: new Date()
        });

        this.addEventListener('load', function() {
          try {
            let responseBody = this.responseText;
            try {
              responseBody = JSON.parse(responseBody);
            } catch (e) {
              // Not JSON, keep as text
              responseBody = responseBody.substring(0, 500) +
                (responseBody.length > 500 ? '...' : '');
            }

            logResponse(this._debugRequestId, {
              status: this.status,
              statusText: this.statusText,
              body: responseBody,
              timestamp: new Date()
            });
          } catch (e) {
            console.error('Debug interceptor error:', e);
          }
        });

        this.addEventListener('error', function(e) {
          logError(this._debugRequestId, e);
        });
      }

      return originalSend.apply(this, arguments);
    };
  }

  function logRequest(requestId, data) {
    const entry = {
      id: requestId,
      type: 'request',
      data,
      response: null
    };

    requestLog.unshift(entry);
    trimLog();
    updateDebugPanel();
  }

  function logResponse(requestId, data) {
    const entry = requestLog.find(item => item.id === requestId);
    if (entry) {
      entry.response = data;
    } else {
      // If request wasn't logged, create a new entry
      requestLog.unshift({
        id: requestId,
        type: 'response',
        response: data
      });
    }

    trimLog();
    updateDebugPanel();
  }

  function logError(requestId, error) {
    const entry = requestLog.find(item => item.id === requestId);
    if (entry) {
      entry.error = {
        message: error.message || String(error),
        stack: error.stack,
        timestamp: new Date()
      };
    } else {
      requestLog.unshift({
        id: requestId,
        type: 'error',
        error: {
          message: error.message || String(error),
          stack: error.stack,
          timestamp: new Date()
        }
      });
    }

    trimLog();
    updateDebugPanel();
  }

  function clearDebugLog() {
    requestLog = [];
    updateDebugPanel();
  }

  function trimLog() {
    if (requestLog.length > MAX_LOG_ENTRIES) {
      requestLog = requestLog.slice(0, MAX_LOG_ENTRIES);
    }
  }

  function updateDebugPanel() {
    if (!isDebugActive) return;

    const debugLog = document.getElementById('debugLog');
    debugLog.innerHTML = '';

    requestLog.forEach(entry => {
      const entryElement = document.createElement('div');
      entryElement.className = `debug-entry ${entry.response ? 'has-response' : ''} ${entry.error ? 'has-error' : ''}`;

      // Request section
      if (entry.data) {
        const requestSection = document.createElement('div');
        requestSection.className = 'debug-request';

        const requestHeader = document.createElement('div');
        requestHeader.className = 'debug-section-header';
        requestHeader.innerHTML = `
          <span class="debug-method">${entry.data.method}</span>
          <span class="debug-url">${entry.data.url}</span>
          <span class="debug-time">${formatTime(entry.data.timestamp)}</span>
        `;

        const requestDetails = document.createElement('div');
        requestDetails.className = 'debug-details';

        // Format request data
        let requestBody = entry.data.body;
        if (requestBody instanceof FormData) {
          const formDataObj = {};
          for (let pair of requestBody.entries()) {
            formDataObj[pair[0]] = pair[1];
          }
          requestBody = formDataObj;
        }

        requestDetails.innerHTML = `
          <pre>${JSON.stringify(requestBody, null, 2) || 'No request body'}</pre>
        `;

        requestSection.appendChild(requestHeader);
        requestSection.appendChild(requestDetails);
        entryElement.appendChild(requestSection);
      }

      // Response section
      if (entry.response) {
        const responseSection = document.createElement('div');
        responseSection.className = 'debug-response';

        const responseHeader = document.createElement('div');
        responseHeader.className = 'debug-section-header';
        responseHeader.innerHTML = `
          <span class="debug-status ${entry.response.status < 400 ? 'success' : 'error'}">
            ${entry.response.status} ${entry.response.statusText}
          </span>
          <span class="debug-time">${formatTime(entry.response.timestamp)}</span>
        `;

        const responseDetails = document.createElement('div');
        responseDetails.className = 'debug-details';
        responseDetails.innerHTML = `
          <pre>${JSON.stringify(entry.response.body, null, 2) || 'No response body'}</pre>
        `;

        responseSection.appendChild(responseHeader);
        responseSection.appendChild(responseDetails);
        entryElement.appendChild(responseSection);
      }

      // Error section
      if (entry.error) {
        const errorSection = document.createElement('div');
        errorSection.className = 'debug-error';

        const errorHeader = document.createElement('div');
        errorHeader.className = 'debug-section-header';
        errorHeader.innerHTML = `
          <span class="debug-error-label">Error</span>
          <span class="debug-time">${formatTime(entry.error.timestamp)}</span>
        `;

        const errorDetails = document.createElement('div');
        errorDetails.className = 'debug-details';
        errorDetails.innerHTML = `
          <pre>${entry.error.message}\n${entry.error.stack || ''}</pre>
        `;

        errorSection.appendChild(errorHeader);
        errorSection.appendChild(errorDetails);
        entryElement.appendChild(errorSection);
      }

      // Add click handler to toggle details
      const headers = entryElement.querySelectorAll('.debug-section-header');
      headers.forEach(header => {
        header.addEventListener('click', function() {
          const details = this.nextElementSibling;
          if (details && details.classList.contains('debug-details')) {
            details.classList.toggle('visible');
          }
        });
      });

      debugLog.appendChild(entryElement);
    });

    if (requestLog.length === 0) {
      const emptyMessage = document.createElement('div');
      emptyMessage.className = 'debug-empty';
      emptyMessage.textContent = 'No requests logged yet';
      debugLog.appendChild(emptyMessage);
    }
  }

  function formatTime(date) {
    if (!date) return '';
    return new Date(date).toLocaleTimeString();
  }

  // Check if panel was previously enabled
  if (localStorage.getItem('debugPanelActive') === 'true') {
    // Wait for DOM to be ready
    window.addEventListener('DOMContentLoaded', function() {
      setTimeout(() => toggleDebugPanel(true), 500);
    });
  }
})();
