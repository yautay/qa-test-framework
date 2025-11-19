  // tests/komputronik-pl/tests/test-account/login_check.js

  const layerLocators = require('../../locators/locators-layers');
  const utils = require('../../../../lib/helpers');
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
        onReadyScript: "../scripts/enter-login-layer.js"
      }
    ]
  };