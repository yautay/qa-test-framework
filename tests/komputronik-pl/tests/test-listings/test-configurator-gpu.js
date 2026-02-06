module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings configurator configurator-gpu html_cache",
            resource: "/advanced-configurator/graphics_card",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings configurator configurator-gpu no_html_cache",
            resource: "/advanced-configurator/graphics_card?a=0",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings configurator configurator-gpu disabled-js",
            resource: "/advanced-configurator/graphics_card",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"]
        },
    ]
};

