// tests/komputronik-pl/tests/test-product-pages/tests-rwd-front-products/test-product-page-54244184.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page html-cache 54244184',
      resource: "/product/54244184",
      delay: 5000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page no-html-cache 54244184',
      resource: '/product/54244184?test=1',
      delay: 5000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
