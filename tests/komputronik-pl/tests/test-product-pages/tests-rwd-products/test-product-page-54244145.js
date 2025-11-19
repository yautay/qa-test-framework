module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl karta_produktu html_cache 54244145',
      resource: "/product/54244145",
      delay: 500,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl karta_produktu no_html_cache 54244145',
      resource: '/product/54244145?test=1',
      delay: 500,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
