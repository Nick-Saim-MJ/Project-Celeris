// Renderiza un .bpmn a SVG y PNG con bpmn-js, en el Chrome/Edge instalado (puppeteer-core, sin descargar Chromium).
// La PNG se toma del SVG que exporta bpmn-js, recortada al diagrama.
// Uso: node render.js <entrada.bpmn> <salida.png> [escala]
const fs = require("fs");
const path = require("path");

const NAVEGADORES = [
  process.env.CHROME_PATH,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
].filter(Boolean);

async function main() {
  const [entrada, salida, escala = "2"] = process.argv.slice(2);
  if (!entrada || !salida) throw new Error("uso: node render.js <entrada.bpmn> <salida.png> [escala]");
  const ejecutable = NAVEGADORES.find((p) => fs.existsSync(p));
  if (!ejecutable) throw new Error("no se encontró Chrome ni Edge; defina CHROME_PATH");
  const puppeteer = (await import("puppeteer-core")).default;

  const visor = path.join(__dirname, "node_modules/bpmn-js/dist/bpmn-viewer.production.min.js");
  const xml = fs.readFileSync(entrada, "utf8");

  const nav = await puppeteer.launch({ executablePath: ejecutable, headless: true });
  try {
    const pag = await nav.newPage();
    await pag.setContent('<html><body style="margin:0"><div id="c" style="width:1200px;height:800px"></div></body></html>');
    await pag.addScriptTag({ path: visor });
    const res = await pag.evaluate(async (x) => {
      const v = new BpmnJS({ container: "#c" });
      const { warnings } = await v.importXML(x);
      const { svg } = await v.saveSVG();
      return { svg, avisos: warnings.map((w) => w.message) };
    }, xml);
    for (const a of res.avisos) console.warn("aviso bpmn-js:", a);
    if (res.avisos.length) throw new Error(`${res.avisos.length} avisos al importar el BPMN`);

    fs.writeFileSync(salida.replace(/\.png$/i, ".svg"), res.svg);

    const m = res.svg.match(/width="([\d.]+)" height="([\d.]+)"/);
    const [w, h] = m ? [Math.ceil(+m[1]), Math.ceil(+m[2])] : [1200, 800];
    await pag.setViewport({ width: w, height: h, deviceScaleFactor: Number(escala) });
    await pag.setContent(`<html><body style="margin:0;background:#fff">${res.svg}</body></html>`);
    const el = await pag.$("svg");
    await el.screenshot({ path: salida, omitBackground: false });
    console.log(`OK ${salida} (${w}x${h} px a escala ${escala})`);
  } finally {
    await nav.close();
  }
}

main().catch((e) => {
  console.error("ERROR:", e.message);
  process.exit(1);
});
