/**
 * Global CSRF Protection for SarfX Application
 * This script automatically adds CSRF token to all fetch requests
 */
(function() {
    'use strict';

    // Get CSRF token from meta tag
    function getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }

    // Store original fetch
    const originalFetch = window.fetch;

    // Override fetch to add CSRF token
    window.fetch = function(url, options = {}) {
        const csrfToken = getCSRFToken();

        // Only add CSRF token for same-origin requests that modify data
        const method = (options.method || 'GET').toUpperCase();
        const modifyingMethods = ['POST', 'PUT', 'DELETE', 'PATCH'];

        if (csrfToken && modifyingMethods.includes(method)) {
            options.headers = options.headers || {};

            // Handle Headers object
            if (options.headers instanceof Headers) {
                if (!options.headers.has('X-CSRFToken')) {
                    options.headers.set('X-CSRFToken', csrfToken);
                }
            } else {
                // Handle plain object
                if (!options.headers['X-CSRFToken']) {
                    options.headers['X-CSRFToken'] = csrfToken;
                }
            }
        }

        return originalFetch.call(this, url, options);
    };

    // Also handle XMLHttpRequest for older code
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url, ...args) {
        this._csrfMethod = method.toUpperCase();
        return originalXHROpen.call(this, method, url, ...args);
    };

    XMLHttpRequest.prototype.send = function(data) {
        const csrfToken = getCSRFToken();
        const modifyingMethods = ['POST', 'PUT', 'DELETE', 'PATCH'];

        if (csrfToken && modifyingMethods.includes(this._csrfMethod)) {
            this.setRequestHeader('X-CSRFToken', csrfToken);
        }

        return originalXHRSend.call(this, data);
    };

    // Log CSRF protection status
    console.log('🔒 CSRF Protection initialized');
})();
