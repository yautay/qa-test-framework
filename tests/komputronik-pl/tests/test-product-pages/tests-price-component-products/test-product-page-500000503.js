// tests/komputronik-pl/tests/test-product-pages/tests-price-component-products/test-product-page-500000503.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page html-cache 500000503',
      resource: "/product/500000503",
      delay: 10000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page no-html-cache 500000503',
      resource: '/product/500000503?test=1',
      delay: 10000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
