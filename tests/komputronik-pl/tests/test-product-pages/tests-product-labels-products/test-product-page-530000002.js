// tests/komputronik-pl/tests/test-product-pages/tests-product-labels-products/test-product-page-530000002.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-product-labels-products html-cache 530000002',
      resource: "/product/530000002",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-product-labels-products no-html-cache 530000002',
      resource: '/product/530000002?a=0',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    }
  ]
};
