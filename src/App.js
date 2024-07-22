import { useCallback, useEffect, useState } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { globalCompletion, localCompletionSource, python, pythonLanguage } from '@codemirror/lang-python';
import { LanguageSupport } from '@codemirror/language';

import ListGroup from "react-bootstrap/ListGroup";

import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';

import { Graphviz } from 'graphviz-react';

import desyncedExport from './desyncedexport.json'
//import desyncedcompiler from './desyncedcompiler.py'
import { ObjectToDesyncedString } from './dsconvert'

import logo from './logo.svg';
import './App.css';

import usePyodide from './usePyodide';




const App = () => {
  const { pyodide, loading, error } = usePyodide();
  const [output, setOutput] = useState('');

  const [writeeditor, setwriteeditor] = useState('');
  const [readeditor, setreadeditor] = useState('');

  const [justincase, setjustincase] = useState('');
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
      }
      ).filter(Boolean);

  const myCompletions = function (context) {
    let word = context.matchBefore(/\w*/)
    if (word.from == word.to && !context.explicit)
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
      const result = pyodide.runPython('python_to_desynced(editortext)', { locals: locals });
      const converted = ObjectToDesyncedString(JSON.parse(result), "C")

      setOutput(converted);
      setCompiling(false);

    }
  };

  const loadExample = async (file) => {
    fetch(`./examples/${file}`)
      .then((r) => r.text())
      .then(text => {
        console.log(text);
        setreadeditor(text);
        setwriteeditor(text);
      })
  }

  const loadInstructions = async () => {

    console.log(pyodide.runPython('square(8)'));
  };


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
  }, [loading]);

  return (
    <div className="App">
      <Container fluid="md">
        <Row>
          <Col>
            <CodeMirror value={writeeditor}
              height="400px"
              align="left"
              onChange={onEditorTextChange}
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
          </Col>
        </Row>

        <Row>
        </Row>
      </Container>



      <div style={{ margin: '10px' }} >
        <button className="btn btn-primary" type="button" disabled={compiling} onClick={runPythonCode}>
          {compiling ? <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" /> : null}
          {compiling ? 'Compiling...' : 'Compile'}
        </button>
      </div>

      <pre align="left">{output}</pre>
      <header className="App-header">
      </header>
    </div>
  );

  function CompileSpinner() {
    return <div className="compilespinner">Loading...</div>;
  }
}

export default App;