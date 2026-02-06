module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings configurator configurator-psu html_cache",
            resource: "/advanced-configurator/power_supply",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings configurator configurator-psu no_html_cache",
            resource: "/advanced-configurator/power_supply?a=0",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings configurator configurator-psu disabled-js",
            resource: "/advanced-configurator/power_supply",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"]
        }
    ]
};
