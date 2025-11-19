// tests/komputronik-pl/tests/test-product-pages/tests-price-component-products/test-product-page-500000502.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-price-component-products html-cache 500000502',
      resource: "/product/500000502",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-price-component-products no-html-cache 500000502',
      resource: '/product/500000502?test=1',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
