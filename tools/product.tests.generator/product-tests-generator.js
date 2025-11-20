// tools/product.tests.generator/product-tests-generator.js
const fs = require("fs");
const path = require("path");

const BASE_DIR = __dirname;
const OUTPUT_ROOT = path.join(BASE_DIR, "..", "..", "tests", "komputronik-pl", "tests", "test-product-pages");
const MANIFEST_BASENAME = ".generated-manifest";
const MANIFEST_FILE = path.join(OUTPUT_ROOT, MANIFEST_BASENAME);
const MANIFEST_JSON_FILE = MANIFEST_FILE + ".json";
const IDS_PREFIX = "ids-";

const TEMPLATE = (id, folderName) => `// tests/komputronik-pl/tests/test-product-pages/${folderName}/test-product-page-${id}.js

module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl product-page ${folderName} html-cache ${id}',
      resource: "/product/${id}",
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl product-page ${folderName} no-html-cache ${id}',
      resource: '/product/${id}?test=1',
      delay: 3000,
      misMatchThreshold: 1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
`;

function getFolderNameFromTxt(filename) {
    const basename = filename.replace(/\.txt$/i, "");
    return basename.startsWith(IDS_PREFIX) ? basename.slice(IDS_PREFIX.length) : basename;
}

function readManifest() {
    try {
        let fileToRead = null;
        if (fs.existsSync(MANIFEST_FILE)) fileToRead = MANIFEST_FILE;
        else if (fs.existsSync(MANIFEST_JSON_FILE)) fileToRead = MANIFEST_JSON_FILE;
        if (!fileToRead) return [];
        const raw = fs.readFileSync(fileToRead, "utf8");
        return JSON.parse(raw);
    } catch (e) {
        console.warn("(i) Nie udało się odczytać manifestu, pomijam czyszczenie.", e.message);
        return [];
    }
}

function writeManifest(entries) {
    try {
        fs.mkdirSync(OUTPUT_ROOT, { recursive: true });
        fs.writeFileSync(MANIFEST_FILE, JSON.stringify(entries, null, 2), "utf8");
        try { if (fs.existsSync(MANIFEST_JSON_FILE)) fs.unlinkSync(MANIFEST_JSON_FILE); } catch (e) {}
    } catch (e) {
        console.warn("(i) Nie udało się zapisać manifestu:", e.message);
    }
}

function removeIfExists(filePath) {
    try {
        if (fs.existsSync(filePath)) {
            const stat = fs.lstatSync(filePath);
            if (stat.isFile()) {
                fs.unlinkSync(filePath);
                return true;
            }
        }
    } catch (e) {
    }
    return false;
}

function removeEmptyDirsUpToRoot(dir) {
    let current = dir;
    while (path.resolve(current).startsWith(path.resolve(OUTPUT_ROOT))) {
        try {
            const files = fs.readdirSync(current);
            if (files.length === 0) {
                fs.rmdirSync(current);
                current = path.dirname(current);
                continue;
            }
        } catch (e) {
            break;
        }
        break;
    }
}

function cleanOldGenerated() {
    const oldEntries = readManifest(); // entries are relative to OUTPUT_ROOT
    if (oldEntries.length === 0) {
        try { if (fs.existsSync(MANIFEST_JSON_FILE)) fs.unlinkSync(MANIFEST_JSON_FILE); } catch (e) {}
        return;
    }

    oldEntries.forEach(rel => {
        const full = path.join(OUTPUT_ROOT, rel);
        const removed = removeIfExists(full);
        if (removed) {
            console.log(`-- usunięto wygenerowany plik: ${path.relative(BASE_DIR, full)}`);
            removeEmptyDirsUpToRoot(path.dirname(full));
        }
    });

    try { if (fs.existsSync(MANIFEST_FILE)) fs.unlinkSync(MANIFEST_FILE); } catch (e) {}
    try { if (fs.existsSync(MANIFEST_JSON_FILE)) fs.unlinkSync(MANIFEST_JSON_FILE); } catch (e) {}
}

function generateFromTxtFile(txtFile, manifestEntries) {
    const txtPath = path.join(BASE_DIR, txtFile);
    const folderName = getFolderNameFromTxt(txtFile);
    const outputDir = path.join(OUTPUT_ROOT, folderName);

    const content = fs.readFileSync(txtPath, "utf8");
    const ids = content
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(line => line.length > 0);

    if (ids.length === 0) {
        console.warn(`(i) Plik ${txtFile} nie zawiera ID, pomijam.`);
        return;
    }

    fs.mkdirSync(outputDir, { recursive: true });

    ids.forEach(id => {
        const filename = `test-product-page-${id}.js`;
        const fileRel = path.join(folderName, filename); // relative to OUTPUT_ROOT
        const filePath = path.join(outputDir, filename);
        const jsContent = TEMPLATE(id, folderName);

        fs.writeFileSync(filePath, jsContent, "utf8");
        manifestEntries.push(fileRel);
        console.log(`✔ ${txtFile} -> ${path.relative(BASE_DIR, filePath)}`);
    });
}

function main() {
    cleanOldGenerated();

    const files = fs.readdirSync(BASE_DIR);
    const txtFiles = files.filter(
        f => f.endsWith(".txt") && fs.lstatSync(path.join(BASE_DIR, f)).isFile()
    );

    if (txtFiles.length === 0) {
        console.warn("Brak plików .txt do przetworzenia.");
        return;
    }

    const manifestEntries = [];

    txtFiles.forEach(f => generateFromTxtFile(f, manifestEntries));

    writeManifest(manifestEntries);
}

main();
