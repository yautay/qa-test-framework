  // tests/komputronik-pl/tests/test-product-pages/test-product-page-54244111.js

  module.exports = {

    scenarios: [
      {
        label: 'komputronik-pl karta_produktu html_cache 54244111',
        resource: "/product/54244111",
        delay: 500,
        misMatchThreshold: 0.1,
        requireSameDimensions: true,
        report: ['browser', 'CI'],
        onReadyScript: '../scripts/close-cookies.js'
      },
      {
        label: 'komputronik-pl karta_produktu no_html_cache 54244111',
        resource: '/product/54244111?test=1',
        delay: 500,
        misMatchThreshold: 0.1,
        requireSameDimensions: true,
        report: ['browser', 'CI'],
        onReadyScript: '../scripts/close-cookies.js'
      }
    ]
  };