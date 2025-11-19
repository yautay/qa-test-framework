// tests/komputronik-pl/tests/test-product-pages/tests-price-component-products/test-product-page-500000501.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page html-cache 500000501',
      resource: "/product/500000501",
      delay: 5000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page no-html-cache 500000501',
      resource: '/product/500000501?test=1',
      delay: 5000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
