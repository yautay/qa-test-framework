// tests/komputronik-pl/tests/test-product-pages/tests-product-labels-products/test-product-page-530000001.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-product-labels-products html-cache 530000001',
      resource: "/product/530000001",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-product-labels-products no-html-cache 530000001',
      resource: '/product/530000001?test=1',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
