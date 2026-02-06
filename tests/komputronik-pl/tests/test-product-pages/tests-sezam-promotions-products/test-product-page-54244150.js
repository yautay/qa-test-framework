// tests/komputronik-pl/tests/test-product-pages/tests-sezam-promotions-products/test-product-page-54244150.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-sezam-promotions-products html-cache 54244150',
      resource: "/product/54244150",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-sezam-promotions-products no-html-cache 54244150',
      resource: '/product/54244150?a=0',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    }
  ]
};
