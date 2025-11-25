// tests/komputronik-pl/tests/test-product-pages/tests-rwd-front-products/test-product-page-54244184.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-rwd-front-products html-cache 54244184',
      resource: "/product/54244184",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-rwd-front-products no-html-cache 54244184',
      resource: '/product/54244184?test=1',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    }
  ]
};
