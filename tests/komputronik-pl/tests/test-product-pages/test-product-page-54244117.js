  // tests/komputronik-pl/tests/test-product-pages/test-product-page-54244117.js

  module.exports = {

    scenarios: [
      {
        label: 'komputronik-pl karta_produktu html_cache 54244117',
        resource: '/product/54244117',
        delay: 500,
        misMatchThreshold: 0.1,
        requireSameDimensions: true,
        report: ['browser', 'CI'],
        onReadyScript: '../scripts/close-cookies.js'
      },
      {
        label: 'komputronik-pl karta_produktu no_html_cache 54244117',
        resource: '/product/54244117?test=1',
        delay: 500,
        misMatchThreshold: 0.1,
        requireSameDimensions: true,
        report: ['browser', 'CI'],
        onReadyScript: '../scripts/close-cookies.js'
      }
    ]
  };