import fs from "fs";
import { buildBlockXML } from "./xml_builder.js";

// Input from Python compiler
const blockTree = JSON.parse(
  fs.readFileSync("../semantic/output/block_tree.json", "utf-8")
);

// Build XML body
const xmlBody = buildBlockXML(blockTree);

// Wrap with Blockly root
const finalXML = `
<xml xmlns="https://developers.google.com/blockly/xml">
${xmlBody}
</xml>
`.trim();

// Write output
fs.mkdirSync("./output", { recursive: true });
fs.writeFileSync("./output/program.xml", finalXML, "utf-8");

console.log("✅ XML generated: assembler/output/program.xml");
