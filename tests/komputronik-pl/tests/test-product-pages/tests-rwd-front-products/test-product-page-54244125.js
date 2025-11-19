// tests/komputronik-pl/tests/test-product-pages/tests-rwd-front-products/test-product-page-54244125.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-rwd-front-products html-cache 54244125',
      resource: "/product/54244125",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-rwd-front-products no-html-cache 54244125',
      resource: '/product/54244125?test=1',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
