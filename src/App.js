import { useCallback, useEffect, useState, useRef } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import {basicSetup, EditorView} from '@uiw/react-codemirror';
import { globalCompletion, localCompletionSource, pyodide, pythonLanguage } from '@codemirror/lang-python';
import { LanguageSupport } from '@codemirror/language';
import * as themes from '@uiw/codemirror-themes-all';


import ListGroup from "react-bootstrap/ListGroup";
import Button from 'react-bootstrap/Button';

import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Alert from 'react-bootstrap/Alert';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';

//import { Graphviz } from 'graphviz-react';

import desyncedExport from './desyncedexport.json'
//import desyncedcompiler from './desyncedcompiler.py'
import { ObjectToDesyncedString } from './dsconvert'

import copy from "copy-to-clipboard";
import './App.css';

import usePyodide from './usePyodide';




const App = () => {
  const { pyodide, loading } = usePyodide();
  const [output, setOutput] = useState('');
  const [compilationSuccess, setCompilationSuccess] = useState(false);

  const editorRef = useRef();

  function editorRefCallack(editor) {
    if (!editorRef.current && editor?.editor && editor?.state && editor?.view) {

      console.log(editor);
      editorRef.current = editor;
    }
  }

 

  const [writeeditor, setwriteeditor] = useState('');
  const [readeditor, setreadeditor] = useState('');

  const [compiling, setCompiling] = useState(false);

  const examples = [
    ["Simple Test", "simple.py"],
    ["Recycle Bot", "Roomba.py"],
    ["Recycle Hub", "RecycleHub.py"],
    ["Radar Tower", "RadarTower.py"],
    ["Build As Needed", "BuildAsNeeded.py"],
  ]

  const formatStringAsFunction = (str) => {
    // Remove whitespace, asterisks, and parentheses
    const cleanedString = str.replace(/[\s*()]/g, '');
    // Lower-case the first letter
    return cleanedString;//.charAt(0).toLowerCase() + cleanedString.slice(1);
  };



  // Completions:
  // N  Logistics Flags: logistics options 
  // Y  Values:          Filterable values from the Information tab
  // N  Frames: 
  // Y  Components:     Mountable Components
  // Y  Items:          
  // N  Visuals:        Tiles
  // Y  Instructions:   Behavioral instructions
  // N  Techs:          Technlogy names
  // N  Update Mapping: Internal versioning patches?

  const instruction_completions =
    Object.keys(desyncedExport["instructions"]).map((key) => {
      if (desyncedExport.instructions[key]["name"])
        return {
          label: formatStringAsFunction(desyncedExport.instructions[key]["name"]),
          detail: desyncedExport.instructions[key]["desc"],
          type: "function",
        }
      return false
    }
    ).filter(Boolean);

    const constants_completions =
    ["values", "components", "items"].flatMap((category) =>
    Object.keys(desyncedExport[category]).map((key) => {
      if (desyncedExport[category][key])
        return {
          label: String(key),
          detail: String(desyncedExport[category][key]["name"]),
          type: "constant",
        }
      return false;
    })
    ).filter(Boolean);


  const myCompletions = function (context) {
    let word = context.matchBefore(/\w*/)
    if (word.from === word.to && !context.explicit)
      return null
    return {
      from: word.from,
      options: [...instruction_completions, ...constants_completions]
    }
  };

  const runPythonCode = async () => {
    if (pyodide) {
      setCompiling(true);
      const locals = pyodide.toPy({ editortext: readeditor })
      const result = pyodide.runPython('python_to_desynced_pyodide(editortext)', { locals: locals });
      const translatedresult = JSON.parse(result);

      console.log("Results:");
      console.log(result);
      console.log(translatedresult);
      console.log(translatedresult[0]);
      setCompilationSuccess(translatedresult[0]);
      if (translatedresult[0])
        setOutput(ObjectToDesyncedString(translatedresult[1], "C"));
      else
        setOutput(translatedresult[1])

      setCompiling(false);

    }
  };

  const loadExample = async (file) => {
    fetch(`./examples/${file}`)
      .then((r) => r.text())
      .then(text => {
        console.log(file);
        console.log(text);
        setreadeditor(text);
        setwriteeditor(text);
      })
  }

  const loadCompiler = async () => {
    setCompiling(true);
    const locals = pyodide.toPy({ test1: desyncedExport });
    console.log(pyodide.runPython(await (await fetch("./desyncedcompiler.py")).text()));
    console.log(pyodide.runPython("import_desynced_ops(path = None, jsonfile=test1)", { locals: locals }));
    setCompiling(false);
  };

  const onEditorTextChange = useCallback((val, viewUpdate) => {
    setreadeditor(val)
  })

  useEffect(() => {
    const setupDScompiler = async () => {
      setCompiling(true);
      if (!loading) {
        console.log("Start Compiler Loadup");
        const locals = pyodide.toPy({ test1: desyncedExport });
        console.log(pyodide.runPython(await (await fetch("./desyncedcompiler.py")).text()));
        console.log(pyodide.runPython("import_desynced_ops(path = None, jsonfile=test1)", { locals: locals }));
        console.log("End Compiler Setup");
        setCompiling(false);
      }
    }
    setupDScompiler();
  }, [loading, pyodide]);

  const handleCopy = () => {
    copy(output)
  }

  const handleClear = () => {
    setreadeditor("");
    setwriteeditor("");
  }

  const OutputAlert = () => (
    <Alert variant={compilationSuccess ? 'success' : 'danger'}
      style={{
        flexWrap: 'wrap',
        wordWrap: 'break-word',
        textAlign: 'left',
      }}
    >
      <Alert.Heading>{compilationSuccess ? 'Compiled Code:' : 'Error:'}</Alert.Heading>
      {output.split('\n').map((line, index) => (
        <div key={index}>{line}</div>
      ))}

    </Alert>
  )

  return (

    <div className="App">
      <div className="d-flex flex-column min-vh-100">
        <Navbar expand="md" className="bg-body-tertiary">
          <Container>
            <Navbar.Brand href="#home">Python Desynced Crosscompiler</Navbar.Brand>

            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse id="basic-navbar-nav">
              <Nav className="me-auto">
              <Nav.Link href="https://stagegames.github.io/DesyncedJavaScriptUtils/" target="_blank">Disassembler</Nav.Link>
              <Nav.Link href="https://github.com/vanweric/PythonToDesyncedCompiler/blob/main/public/Info.md" target="_blank">Info</Nav.Link>
                <Nav.Link href="https://github.com/vanweric/PythonToDesyncedCompiler" target="_blank">GitHub</Nav.Link>
                <Nav.Link href="https://www.youtube.com/@VDubBuilds" target="_blank">YouTube</Nav.Link>

                <NavDropdown title="Examples " id="basic-nav-dropdown">
                  {
                    examples.map((item, ix) => (
                      <NavDropdown.Item action onClick={() => loadExample(item[1])} disabled={compiling} key={ix}>
                        {item[0]}
                      </NavDropdown.Item>
                    ))
                  }
                  <NavDropdown.Divider />
                  <NavDropdown.Item href="https://github.com/vanweric/PythonToDesyncedCompiler/tree/main/public/examples" target="_blank">
                    Examples Folder
                  </NavDropdown.Item>
                </NavDropdown>
              </Nav>

              <Nav className="ms-auto">
              <Button variant="secondary"  disabled={!compilationSuccess} onClick={handleCopy} style={{ marginRight: '5px' }}>
                  {compiling ? <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" /> : null}
                  {compiling ? 'Compiling...' : 'Copy'}
                </Button>

                <Button variant="secondary"  disabled={compiling} onClick={handleClear} style={{ marginRight: '5px' }}>
                  {compiling ? <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" /> : null}
                  {compiling ? 'Compiling...' : 'Clear'}
                </Button>

                <Button variant="primary"  disabled={compiling} onClick={runPythonCode} style={{ marginRight: '5px' }}>
                  {compiling ? <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" /> : null}
                  {compiling ? 'Compiling...' : 'Compile'}
                </Button>
              </Nav>
            </Navbar.Collapse>
          </Container>
        </Navbar>

        <Container fluid="xl">
        <div className="p-4 bg-white border rounded shadow-sm" overflow-y="auto">

              <CodeMirror value={writeeditor}
                className="cm-outer-container"
                align="left"
                height="400px"
                onChange={onEditorTextChange}
                ref={editorRefCallack}
                //extensions={[python()]}
                theme = {themes.githubLight}
                extensions={ [
                  new LanguageSupport(pythonLanguage, [
                    pythonLanguage.data.of({ autocomplete: localCompletionSource }),
                    pythonLanguage.data.of({ autocomplete: globalCompletion }),
                    pythonLanguage.data.of({ autocomplete: myCompletions }),
                  ]),
                  EditorView.lineWrapping]
                }
                disabled={compiling} /
              >
                  </div>
              
        </Container>

        {output ? <OutputAlert /> : null}



        <footer className="bg-light py-3 mt-auto">
          <Container>
            <p className="text-center mb-1">
              Copyright © 2024 by Eric VanWyk
            </p>
            <p className="text-center small text-muted">
              This compiler is freely available under the{' '}
              <a
                href="https://opensource.org/licenses/MIT"
                target="_blank"
                rel="noopener noreferrer"
              >
                MIT License
              </a>
            </p>
          </Container>
        </footer>
      </div>
    </div>

    
  );
}

export default App;