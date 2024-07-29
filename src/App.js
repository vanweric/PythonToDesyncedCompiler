import { useCallback, useEffect, useState, useRef } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { globalCompletion, localCompletionSource, pyodide, pythonLanguage } from '@codemirror/lang-python';
import { LanguageSupport } from '@codemirror/language';

import ListGroup from "react-bootstrap/ListGroup";

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

  const runTestCode = () => {
    console.log(editorRef)
    editorRef.current.editor.markText({line:3})
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
    Object.keys(desyncedExport["items"]).map((key) => {
      if (desyncedExport.items[key])
        return {
          label: String(key),
          detail: String(desyncedExport.items[key]["name"]),
          type: "keyword",
        }
      return false;
    }
    ).filter(Boolean);

  const components_completions =
    Object.keys(desyncedExport["components"]).map((key) => {
      if (desyncedExport.components[key])
        return {
          label: String(key),
          detail: String(desyncedExport.components[key]["name"]),
          type: "keyword",
        }
      return false;
    }
    ).filter(Boolean);

  const myCompletions = function (context) {
    let word = context.matchBefore(/\w*/)
    if (word.from === word.to && !context.explicit)
      return null
    return {
      from: word.from,
      options: [...instruction_completions, ...components_completions, ...constants_completions]
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
      <Navbar expand="lg" className="bg-body-tertiary">
        <Container>
          <Navbar.Brand href="#home">Python Desynced Crosscompiler</Navbar.Brand>

          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav className="me-auto">
              <Nav.Link href="#home">Info</Nav.Link>
              <Nav.Link href="https://github.com/vanweric/PythonToDesyncedCompiler" target="_blank">GitHub</Nav.Link>
              <Nav.Link href="https://www.youtube.com/@VDubBuilds" target="_blank">YouTube</Nav.Link>

              <NavDropdown title="Examples Go Here Instead??" id="basic-nav-dropdown">
                <NavDropdown.Item href="#action/3.1">Action</NavDropdown.Item>
                <NavDropdown.Item href="#action/3.2">
                  Another action
                </NavDropdown.Item>
                <NavDropdown.Item href="#action/3.3">Something</NavDropdown.Item>
                <NavDropdown.Divider />
                <NavDropdown.Item href="#action/3.4">
                  Separated link
                </NavDropdown.Item>
              </NavDropdown>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <Container fluid="md">
        <Row>
          <Col>
            <CodeMirror value={writeeditor}
              height="400px"
              align="left"
              onChange={onEditorTextChange}
              ref={editorRefCallack}
              //extensions={[python()]}
              extensions={
                new LanguageSupport(pythonLanguage, [
                  pythonLanguage.data.of({ autocomplete: localCompletionSource }),
                  pythonLanguage.data.of({ autocomplete: globalCompletion }),
                  pythonLanguage.data.of({ autocomplete: myCompletions }),
                ])
              }
              disabled={compiling} /
            >
          </Col>
          <Col md="auto">
            Examples
            <ListGroup>
              {
                examples.map((item, ix) => (
                  <ListGroup.Item action onClick={() => loadExample(item[1])} disabled={compiling} key={ix}>
                    {item[0]}
                  </ListGroup.Item>
                ))
              }
            </ListGroup>

            <div style={{ margin: '10px' }} >
              <button className="btn btn-primary" type="button" disabled={compiling} onClick={runPythonCode}>
                {compiling ? <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" /> : null}
                {compiling ? 'Compiling...' : 'Compile'}
              </button>
            </div> 
            
            <div style={{ margin: '10px' }} >
              <button className="btn btn-primary" type="button"  onClick={runTestCode}>
                TEST
              </button>
            </div>

          </Col>
        </Row>

        <Row>
        </Row>
      </Container>





      {output ? <OutputAlert /> : null}

      <header className="App-header">
      </header>
    </div>
  );
}

export default App;