// tests/komputronik-pl/tests/test-product-pages/tests-demo-bugs/test-product-page-914916.js
// https://jira.netcorner.pl/browse/NN-22565
// https://jira.netcorner.pl/browse/NN-22757

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-demo-bugs html-cache 914916',
      resource: "/product/914916",
      delay: 10000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-demo-bugs no-html-cache 914916',
      resource: '/product/914916?test=1',
      delay: 10000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
