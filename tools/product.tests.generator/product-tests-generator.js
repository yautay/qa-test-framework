const fs = require("fs");
const path = require("path");

// ====== USTAWIENIA ======
const IDS_FILE = "./ids.txt";      // plik z listą ID
const OUTPUT_DIR = "./generated";  // folder wyjściowy
// ========================

const TEMPLATE = (id) => `module.exports = {
  scenarios: [
    {
      label: 'komputronik-pl karta_produktu html_cache ${id}',
      resource: "/product/${id}",
      delay: 500,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    },
    {
      label: 'komputronik-pl karta_produktu no_html_cache ${id}',
      resource: '/product/${id}?test=1',
      delay: 500,
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      report: ['browser', 'CI'],
      onReadyScript: '../scripts/close-cookies.js'
    }
  ]
};
`;

function main() {
    if (!fs.existsSync(IDS_FILE)) {
        console.error(`❌ Brak pliku: ${IDS_FILE}`);
        return;
    }

    const content = fs.readFileSync(IDS_FILE, "utf8");
    const ids = content
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(line => line.length > 0);

    if (!fs.existsSync(OUTPUT_DIR)) {
        fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    ids.forEach(id => {
        const filename = `test-product-page-${id}.js`;
        const filepath = path.join(OUTPUT_DIR, filename);
        const jsContent = TEMPLATE(id);

        fs.writeFileSync(filepath, jsContent, "utf8");
        console.log(`✔ Wygenerowano: ${filepath}`);
    });
}

main();
