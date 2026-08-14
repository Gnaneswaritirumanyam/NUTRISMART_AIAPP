let API_BASE_URL = "http://10.113.224.191:8000";

window.API_BASE_URL = API_BASE_URL;

async function apiFetch(endpoint, options = {}, retries = 3) {
    let normalized = endpoint;
    if (normalized.startsWith("./")) {
        normalized = normalized.slice(1);
    }
    if (!normalized.startsWith("/")) {
        normalized = "/" + normalized;
    }
    
    // Fallback IPs for both Capacitor and regular WebView (physical device vs emulator)
    const baseUrlsToTry = [
        "http://10.113.224.191:8000",
        "http://10.0.2.2:8000",
        "http://127.0.0.1:8000"
    ];

    const defaultOptions = {
        credentials: "include",
        headers: {}
    };

    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    };

    // Attach JWT token if available
    const token = localStorage.getItem("access_token");
    if (token) {
        finalOptions.headers.Authorization = `Bearer ${token}`;
    }

    let lastError = null;

    for (let i = 0; i < retries; i++) {
        for (let baseUrl of baseUrlsToTry) {
            const url = endpoint.startsWith("http")
                ? endpoint
                : `${baseUrl}${normalized}`;
            
            try {
                const response = await fetch(url, finalOptions);

                if (response.status === 401) {
                    // Handle unauthorized globally
                    localStorage.removeItem("access_token");
                    window.location.href = "./login.html";
                    return response;
                }
                
                // If we succeeded, update the global base URL to the working one (speeds up future requests)
                if (window.Capacitor) {
                    window.API_BASE_URL = baseUrl;
                }
                
                return response;
            } catch (error) {
                console.warn(`API request failed for ${url} (attempt ${i + 1}):`, error);
                lastError = error;
            }
        }
        
        // Wait before retrying (exponential backoff: 500ms, 1000ms, etc.)
        if (i < retries - 1) {
            await new Promise(resolve => setTimeout(resolve, 500 * (i + 1)));
        }
    }

    console.error("All API request attempts failed:", { endpoint, lastError });
    throw lastError;
}
window.apiFetch = apiFetch;

// Android Hardware Back Button Handler
document.addEventListener('DOMContentLoaded', () => {
  if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {
    window.Capacitor.Plugins.App.addListener('backButton', ({canGoBack}) => {
      if (canGoBack) {
        window.history.back();
      } else {
        window.Capacitor.Plugins.App.exitApp();
      }
    });
  }
});
