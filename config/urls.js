// config/urls.js


const serverTypeTest = "test"; // "prod", "demo", "test"
const serverTypeReference = "test"; // "prod", "demo", "test"

const hardcodedUrlsProd = {
    komputronik: "https://komputronik.pl",
    dktr: "https://d.ktr.pl",
};

const hardcodedUrlsDemo = {
    komputronik: "https://sklep3-demo.komputronik.dev",
    dktr: "https://ktr-demo.ktr.pl",
};

function buildUrl(channel, hosts) {
    let testUrl, referenceUrl;

    if (channel === "komputronik-pl") {
        channel = "komputronik";
    }

    if (serverTypeTest === "prod" && hardcodedUrlsProd[channel]) {
        testUrl = hardcodedUrlsProd[channel];
    } else if (serverTypeTest === "demo" && hardcodedUrlsDemo[channel]) {
        testUrl = hardcodedUrlsDemo[channel];
    } else {
        testUrl = `https://${channel}-${hosts.test}.netcorner.pl`;
    }

    if (serverTypeReference === "prod" && hardcodedUrlsProd[channel]) {
        referenceUrl = hardcodedUrlsProd[channel];
    } else if (serverTypeReference === "demo" && hardcodedUrlsDemo[channel]) {
        referenceUrl = hardcodedUrlsDemo[channel];
    } else {
        referenceUrl = `https://${channel}-${hosts.reference}.netcorner.pl`;
    }

    return { testUrl, referenceUrl };
}

module.exports = {
    serverTypeTest,
    serverTypeReference,
    hardcodedUrlsProd,
    hardcodedUrlsDemo,
    buildUrl,
};
