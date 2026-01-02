/**
 * Blockly block type mapping (IR → Blockly)
 */
const BLOCK_TYPE_MAP = {
  essentials_var_set: "variables_set",
  essentials_var_get: "variables_get",
  essentials_num_literal: "math_number",
  essentials_num_arithmetic: "math_arithmetic",
  essentials_compare: "logic_compare",
  essentials_logic_and: "logic_operation",
  essentials_logic_or: "logic_operation",
  control_if_truthy: "controls_if",
  text_literal: "text",
  text_print: "text_print",
};

/**
 * Operator mappings
 */
const ARITHMETIC_OP_MAP = {
  "+": "ADD",
  "-": "MINUS",
  "*": "MULTIPLY",
  "/": "DIVIDE",
};

const COMPARE_OP_MAP = {
  "==": "EQ",
  "!=": "NEQ",
  "<": "LT",
  "<=": "LTE",
  ">": "GT",
  ">=": "GTE",
};

/**
 * Recursively converts a validated block tree into Blockly XML
 * @param {Object} block
 * @returns {string}
 */
export function buildBlockXML(block) {
  if (!block || typeof block !== "object") {
    throw new Error("Invalid block node");
  }

  if (!block.type) {
    throw new Error("Block missing type");
  }

  // Map block type
  const blockType = BLOCK_TYPE_MAP[block.type] ?? block.type;

  let xml = `<block type="${blockType}">`;

  // Fields
  if (block.fields) {
    for (let [name, value] of Object.entries(block.fields)) {
      // Arithmetic operator mapping
      if (block.type === "essentials_num_arithmetic" && name === "OP") {
        value = ARITHMETIC_OP_MAP[value] ?? value;
      }

      // Comparison operator mapping
      if (block.type === "essentials_compare" && name === "OP") {
        value = COMPARE_OP_MAP[value] ?? value;
      }

      // Logic AND / OR mapping
      if (
        (block.type === "essentials_logic_and" ||
          block.type === "essentials_logic_or") &&
        name === "OP"
      ) {
        value = block.type === "essentials_logic_and" ? "AND" : "OR";
      }

      xml += `<field name="${name}">${String(value)}</field>`;
    }
  }

  // Value inputs
  if (block.value_inputs) {
    for (const [name, child] of Object.entries(block.value_inputs)) {
      xml += `<value name="${name}">`;
      xml += buildBlockXML(child);
      xml += `</value>`;
    }
  }

  // Statement inputs
  if (block.statement_inputs) {
    for (const [name, child] of Object.entries(block.statement_inputs)) {
      xml += `<statement name="${name === "THEN" ? "DO" : name}">`;
      xml += buildBlockXML(child);
      xml += `</statement>`;
    }
  }

  // Sequential blocks
  if (block.next) {
    xml += `<next>`;
    xml += buildBlockXML(block.next);
    xml += `</next>`;
  }

  xml += `</block>`;
  return xml;
}
