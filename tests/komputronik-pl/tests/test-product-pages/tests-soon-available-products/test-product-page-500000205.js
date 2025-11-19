// tests/komputronik-pl/tests/test-product-pages/tests-soon-available-products/test-product-page-500000205.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-soon-available-products html-cache 500000205',
      resource: "/product/500000205",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-soon-available-products no-html-cache 500000205',
      resource: '/product/500000205?test=1',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
