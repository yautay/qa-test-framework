// config/urls.js


const serverTypeTest = "test"; // "prod", "demo", "test"
const serverTypeReference = "test"; // "prod", "demo", "test"

const hostReference = "sztos.alfa";
const testHost = "selenium.alfa";

const hardcodedUrlsProd = {
    komputronikPl: "https://komputronik.pl",
    dktr: "https://d.ktr.pl",
};

const hardcodedUrlsDemo = {
    komputronikPl: "https://sklep3-demo.komputronik.dev",
    dktr: "https://ktr-demo.ktr.pl",
};

function buildUrl(channel) {
    let testUrl, referenceUrl;

    if (serverTypeTest === "prod" && hardcodedUrlsProd[channel]) {
        testUrl = hardcodedUrlsProd[channel];
    } else if (serverTypeTest === "demo" && hardcodedUrlsDemo[channel]) {
        testUrl = hardcodedUrlsDemo[channel];
    } else {
        testUrl = `https://${channel}-${testHost}.netcorner.pl`;
    }

    if (serverTypeReference === "prod" && hardcodedUrlsProd[channel]) {
        referenceUrl = hardcodedUrlsProd[channel];
    } else if (serverTypeReference === "demo" && hardcodedUrlsDemo[channel]) {
        referenceUrl = hardcodedUrlsDemo[channel];
    } else {
        referenceUrl = `https://${channel}-${hostReference}.netcorner.pl`;
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
