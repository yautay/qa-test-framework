// tests/komputronik-pl/tests/test-product-pages/tests-soon-available-products/test-product-page-500000207.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-soon-available-products html-cache 500000207',
      resource: "/product/500000207",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-soon-available-products no-html-cache 500000207',
      resource: '/product/500000207?test=1',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    }
  ]
};
