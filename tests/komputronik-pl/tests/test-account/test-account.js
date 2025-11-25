  // tests/komputronik-pl/tests/test-account/login_check.js

  const layerLocators = require('../../locators/locators-layers');
  module.exports = {
    defaultResource: "/",

    scenarios: [
      {
        label: "komputronik-pl Sprawdzenie logowania",
        selectors: [layerLocators.loginLayer],
        selectorExpansion: false,
        delay: 500,
        misMatchThreshold: 0.1,
        requireSameDimensions: true,
        report: ["browser", "CI"],
        onReadyScript: "./../../tests/komputronik-pl/scripts/enter-login-layer.js"
      }
    ]
  };