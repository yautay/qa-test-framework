// tests/komputronik-pl/tests/test-product-pages/tests-sezam-promotions-products/test-product-page-54244151.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-sezam-promotions-products html-cache 54244151',
      resource: "/product/54244151",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-sezam-promotions-products no-html-cache 54244151',
      resource: '/product/54244151?test=1',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
