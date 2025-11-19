const fs = require("fs");
const path = require("path");

const BASE_DIR = __dirname;

const IDS_PREFIX = "ids-";

const TEMPLATE = (id, folderName) => `// tests/komputronik-pl/tests/test-product-pages/${folderName}/test-product-page-${id}.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page html-cache ${id}',
      resource: "/product/${id}",
      delay: 10000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page no-html-cache ${id}',
      resource: '/product/${id}?test=1',
      delay: 10000,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
`;

function getFolderNameFromTxt(filename) {
    const basename = filename.replace(/\.txt$/i, "");
    return basename.startsWith(IDS_PREFIX)
        ? basename.slice(IDS_PREFIX.length)
        : basename;
}

function generateFromTxtFile(txtFile) {
    const txtPath = path.join(BASE_DIR, txtFile);
    const folderName = getFolderNameFromTxt(txtFile);
    const outputDir = path.join(BASE_DIR, 'generated', folderName);

    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const content = fs.readFileSync(txtPath, "utf8");
    const ids = content
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(line => line.length > 0);

    if (ids.length === 0) {
        console.warn(`(i) Plik ${txtFile} nie zawiera ID, pomijam.`);
        return;
    }

    ids.forEach(id => {
        const filename = `test-product-page-${id}.js`;
        const filePath = path.join(outputDir, filename);
        const jsContent = TEMPLATE(id, folderName);

        fs.writeFileSync(filePath, jsContent, "utf8");
        console.log(`✔ ${txtFile} -> ${path.relative(BASE_DIR, filePath)}`);
    });
}

function main() {
    const files = fs.readdirSync(BASE_DIR);

    const txtFiles = files.filter(
        f =>
            f.endsWith(".txt") &&
            fs.lstatSync(path.join(BASE_DIR, f)).isFile()
    );

    if (txtFiles.length === 0) {
        console.warn("Brak plików .txt do przetworzenia.");
        return;
    }

    txtFiles.forEach(generateFromTxtFile);
}

main();
