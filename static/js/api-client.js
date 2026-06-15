var ApiClient = {
  _request: async function(url, options) {
    if (!options) options = {};
    var headers = {
      "Content-Type": "application/json",
    };
    if (options.headers) {
      for (var key in options.headers) {
        headers[key] = options.headers[key];
      }
    }

    try {
      var response = await fetch(url, Object.assign({}, options, { headers: headers }));

      if (response.status === 401) {
        console.warn("[Security] Session expired. Redirecting...");
        window.location.href = "/login";
        return new Promise(function() {});
      }

      var contentType = response.headers.get("content-type");
      if (contentType && contentType.indexOf("application/json") === -1)
        return response;

      var data = await response.json();
      if (!response.ok)
        throw new Error(data.error || "HTTP Error: " + response.status);
      return data;
    } catch (error) {
      console.error("[ApiClient] " + (options.method || "GET") + " " + url + " failed:", error.message);
      throw error;
    }
  },

  get: function(url) {
    return this._request(url, { method: "GET" });
  },

  post: function(url, data) {
    return this._request(url, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  put: function(url, data) {
    return this._request(url, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  delete: function(url) {
    return this._request(url, { method: "DELETE" });
  },
};
