// tests/komputronik-pl/tests/test-product-pages/tests-price-component-products/test-product-page-500000501.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page tests-price-component-products html-cache 500000501 smoke',
      resource: "/product/500000501",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page tests-price-component-products no-html-cache 500000501',
      resource: '/product/500000501?a=0',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser'],
      onReadyScript: './../../tests/komputronik-pl/scripts/close-cookies.js'
    }
  ]
};
