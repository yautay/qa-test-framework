  // tests/komputronik-pl/tests/test-product-pages/test-product-page-54244113.js

  module.exports = {

    scenarios: [
      {
        label: 'komputronik-pl karta_produktu html_cache 54244113',
        resource: '/product/54244113',
        delay: 500,
        misMatchThreshold: 0.1,
        requireSameDimensions: true,
        report: ['browser', 'CI'],
        onReadyScript: '../scripts/close-cookies.js'
      },
      {
        label: 'komputronik-pl karta_produktu no_html_cache 54244113',
        resource: '/product/54244113?test=1',
        delay: 500,
        misMatchThreshold: 0.1,
        requireSameDimensions: true,
        report: ['browser', 'CI'],
        onReadyScript: '../scripts/close-cookies.js'
      }
    ]
  };