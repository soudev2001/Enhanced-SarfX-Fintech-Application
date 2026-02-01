/**
 * Global CSRF Protection for SarfX Application
 * Automatically injects CSRF token into all fetch() and XMLHttpRequest requests
 */
(function() {
    'use strict';

    // Get CSRF token from meta tag
    function getCSRFToken() {
        var metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }

    // Expose helper for manual use
    window.SarfXCSRF = {
        getToken: getCSRFToken,
        getHeader: function() {
            return { 'X-CSRFToken': getCSRFToken() };
        }
    };

    var MODIFYING_METHODS = ['POST', 'PUT', 'DELETE', 'PATCH'];

    function isModifyingMethod(method) {
        return MODIFYING_METHODS.indexOf((method || 'GET').toUpperCase()) !== -1;
    }

    function isSameOrigin(url) {
        if (!url) return true;
        if (typeof url === 'string') {
            if (url.charAt(0) === '/' || url.indexOf('./') === 0 || url.indexOf('../') === 0) return true;
            try {
                var parsed = new URL(url, window.location.origin);
                return parsed.origin === window.location.origin;
            } catch (e) {
                return true;
            }
        }
        // Request object
        if (url instanceof Request) {
            try {
                var reqUrl = new URL(url.url);
                return reqUrl.origin === window.location.origin;
            } catch (e) {
                return true;
            }
        }
        return true;
    }

    // === FETCH OVERRIDE ===
    var originalFetch = window.fetch;

    window.fetch = function(input, init) {
        init = init || {};
        var method = 'GET';
        var url = input;

        // Handle Request objects
        if (input instanceof Request) {
            method = input.method || 'GET';
            url = input.url;
        }
        if (init.method) {
            method = init.method;
        }

        method = method.toUpperCase();
        var csrfToken = getCSRFToken();

        if (csrfToken && isModifyingMethod(method) && isSameOrigin(url)) {
            if (!init.headers) {
                init.headers = {};
            }
            // Convert Headers object to plain object if needed
            if (init.headers instanceof Headers) {
                var plain = {};
                init.headers.forEach(function(value, key) {
                    plain[key] = value;
                });
                init.headers = plain;
            }
            // Add CSRF token if not already present
            if (!init.headers['X-CSRFToken'] && !init.headers['x-csrftoken']) {
                init.headers['X-CSRFToken'] = csrfToken;
            }
        }

        return originalFetch.call(this, input, init);
    };

    // === XMLHttpRequest OVERRIDE ===
    var originalXHROpen = XMLHttpRequest.prototype.open;
    var originalXHRSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url) {
        this._csrfMethod = (method || 'GET').toUpperCase();
        this._csrfUrl = url;
        return originalXHROpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function(data) {
        var csrfToken = getCSRFToken();
        if (csrfToken && isModifyingMethod(this._csrfMethod) && isSameOrigin(this._csrfUrl)) {
            try {
                this.setRequestHeader('X-CSRFToken', csrfToken);
            } catch (e) {
                // setRequestHeader may throw if called at wrong state
            }
        }
        return originalXHRSend.apply(this, arguments);
    };

    console.log('[SarfX] CSRF Protection initialized');
})();
