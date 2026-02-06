// tests/komputronik-pl/tests/test-product-pages/tests-demo-bugs/test-product-page-914916.js
// https://jira.netcorner.pl/browse/NN-22565
// https://jira.netcorner.pl/browse/NN-22757

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-demo-bugs html-cache 914916 smoke',
      resource: "/product/914916",
      delay: 10000,
      misMatchThreshold: 0.5,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-demo-bugs no-html-cache 914916',
      resource: '/product/914916?a=0',
      delay: 10000,
      misMatchThreshold: 0.5,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    }
  ]
};
