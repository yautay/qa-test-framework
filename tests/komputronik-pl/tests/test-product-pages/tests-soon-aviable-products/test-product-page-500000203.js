module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl karta_produktu html_cache 500000203',
      resource: "/product/500000203",
      delay: 500,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl karta_produktu no_html_cache 500000203',
      resource: '/product/500000203?test=1',
      delay: 500,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
