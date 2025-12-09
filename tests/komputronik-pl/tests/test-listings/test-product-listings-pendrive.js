module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings product-listing pendrives promotion-labels html_cache",
            resource: "/category/686/pendrive.html",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings product-listing pendrives promotion-labels no_html_cache",
            resource: "/category/686/pendrive.html?p=2",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings product-listing pendrives promotion-labels no_html_cache",
            resource: "/category/686/pendrive.html?p=4",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings product-listing pendrives disabled-js",
            resource: "/category/686/pendrive.html",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
        },
        {
            label: "komputronik-pl listings product-listing pendrives no_html_cache",
            resource: "category/686/pendrive.html?test=1",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        }
    ]
};
