// tests/komputronik_pl/tests/test_home_page/home_page_suite.js

module.exports = {
  defaultResource: "/",

  scenarios: [
    {
      label: "komputronik_pl home_page navigation_bar html_cache",
      selectors: [],
      delay: 500,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ["browser", "CI"],
      onReadyScript: "closeCookies.js"
    },

    {
      label: "komputronik_pl home_page navigation_bar no_html_cache",
      resource: "/?test=1",
      selectors: [],
      delay: 500,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ["browser", "CI"],
      onReadyScript: "closeCookies.js"
    }
  ]
};

