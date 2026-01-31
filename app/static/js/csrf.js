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
            // Ensure headers exist as an object
            if (!options.headers) {
                options.headers = {};
            }

            // Convert Headers object to plain object if needed
            if (options.headers instanceof Headers) {
                const plainHeaders = {};
                options.headers.forEach((value, key) => {
                    plainHeaders[key] = value;
                });
                options.headers = plainHeaders;
            }

            // Add CSRF token if not already present
            if (!options.headers['X-CSRFToken']) {
                options.headers['X-CSRFToken'] = csrfToken;

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
