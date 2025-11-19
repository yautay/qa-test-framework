// tests/komputronik-pl/tests/test-product-pages/tests-rwd-front-products/test-product-page-54244156.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page html-cache 54244156',
      resource: "/product/54244156",
      delay: 10000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page no-html-cache 54244156',
      resource: '/product/54244156?test=1',
      delay: 10000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
