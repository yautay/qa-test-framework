// tests/komputronik-pl/tests/test-product-pages/tests-sezam-promotions-products/test-product-page-54244157.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-sezam-promotions-products html-cache 54244157',
      resource: "/product/54244157",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-sezam-promotions-products no-html-cache 54244157',
      resource: '/product/54244157?a=0',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    }
  ]
};
