  // tests/komputronik_pl/tests/test_account/login_check.js

  const layerLocators = require('../../locators/locatorsLayers');
  const utils = require('../../../../lib/helpers');
  module.exports = {
    defaultResource: "/",

    scenarios: [
      {
        label: "komputronik_pl Sprawdzenie logowania",
        selectors: [layerLocators.loginLayer],
        selectorExpansion: false,
        delay: 500,
        misMatchThreshold: 0.1,
        requireSameDimensions: true,
        report: ["browser", "CI"],
        onReadyScript: "../scripts/enterLoginLayer.js"
      }
    ]
  };