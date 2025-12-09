module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings configurator configurator-motherboard html_cache",
            resource: "/advanced-configurator/motherboard",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings configurator configurator-motherboard no_html_cache",
            resource: "/advanced-configurator/motherboard?test=1",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings configurator configurator-motherboard disabled-js",
            resource: "/advanced-configurator/motherboard",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"]
        }
    ]
};
