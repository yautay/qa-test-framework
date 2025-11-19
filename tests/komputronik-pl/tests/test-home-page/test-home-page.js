// tests/komputronik-pl/tests/test-home-page/test-home-page.js

module.exports = {
  defaultResource: "/",

  scenarios: [
    {
      label: "komputronik-pl home_page navigation_bar html_cache",
      selectors: [],
      delay: 500,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ["browser", "CI"],
      onReadyScript: "close-cookies.js"
    },

    {
      label: "komputronik-pl home_page navigation_bar no_html_cache",
      resource: "/?test=1",
      selectors: [],
      delay: 500,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ["browser", "CI"],
      onReadyScript: "close-cookies.js"
    }
  ]
};

