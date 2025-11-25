// tests/komputronik-pl/tests/test-product-pages/tests-rwd-front-products/test-product-page-54244130.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-rwd-front-products html-cache 54244130',
      resource: "/product/54244130",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-rwd-front-products no-html-cache 54244130',
      resource: '/product/54244130?test=1',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    }
  ]
};
