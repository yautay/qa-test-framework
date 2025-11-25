function makeTimestampName() {
    const d = new Date();
    const pad = (n) => n.toString().padStart(2, '0');
    return `run_${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

module.exports = makeTimestampName;
