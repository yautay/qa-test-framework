module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings product-listing laptops html_cache smoke",
            resource: "/category/5022/laptopy.html",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings product-listing laptops no_html_cache",
            resource: "/category/5022/laptopy.html?p=2",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings product-listing laptops disabled-js",
            resource: "/category/5022/laptopy.html",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
        },
        {
            label: "komputronik-pl listings product-listing laptops no_html_cache",
            resource: "/category/5022/laptopy.html?test=1",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        }
    ]
};
