// Create workspace
const workspace = Blockly.inject("blocklyDiv", {
    toolbox: `<xml></xml>` // empty toolbox (we load XML directly)
  });
  
  // Load XML from file
  async function loadAndRun() {
    const response = await fetch("./program.xml");
    const xmlText = await response.text();
  
    const dom = Blockly.utils.xml.textToDom(xmlText);
    Blockly.Xml.domToWorkspace(dom, workspace);
  
    // Generate Python code
    const pythonCode = Blockly.Python.workspaceToCode(workspace);
  
    console.log("===== GENERATED PYTHON =====");
    console.log(pythonCode);
    console.log("============================");
  
    // Optional: expose globally
    window.generatedPython = pythonCode;
  }
  
  loadAndRun();
  