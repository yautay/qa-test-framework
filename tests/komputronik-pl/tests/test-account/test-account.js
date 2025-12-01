  // tests/komputronik-pl/tests/test-account/login_check.js

  const layerLocators = require('../../locators/locators-layers');
  module.exports = {
    defaultResource: "/",

    scenarios: [
      {
        label: "komputronik-pl login-layer",
        selectors: [layerLocators.loginLayer],
        selectorExpansion: false,
        delay: 500,
        misMatchThreshold: 1,
        requireSameDimensions: true,
        report: ["browser"],
        onReadyScript: "./../../tests/komputronik-pl/scripts/enter-login-layer.js"
      }
    ]
  };