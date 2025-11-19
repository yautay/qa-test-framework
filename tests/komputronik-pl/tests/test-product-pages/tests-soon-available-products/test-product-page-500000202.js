// tests/komputronik-pl/tests/test-product-pages/tests-soon-available-products/test-product-page-500000202.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page html-cache 500000202',
      resource: "/product/500000202",
      delay: 10000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page no-html-cache 500000202',
      resource: '/product/500000202?test=1',
      delay: 10000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
