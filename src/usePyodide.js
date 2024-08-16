import { useEffect, useState } from "react";

const usePyodide = () => {
  const [pyodide, setPyodide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadPyodide = async () => {
      try {
        console.log("Start Pyodide Load");
        const script = document.createElement("script");
        //script.src = 'https://cdn.jsdelivr.net/pyodide/v0.23.2/full/pyodide.js';
        script.src = "https://cdn.jsdelivr.net/pyodide/v0.26.1/full/pyodide.js";
        script.onload = async () => {
          const pyodide = await window.loadPyodide({
            //indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.23.2/full/',
            indexURL: "https://cdn.jsdelivr.net/pyodide/v0.26.1/full/",
          });
          setPyodide(pyodide);
          setLoading(false);
          console.log("End Pyodide Load");
        };
        document.head.appendChild(script);
      } catch (err) {
        console.log(err);
        setError(err);
        setLoading(false);
      }
    };

    loadPyodide();
  }, []);

  return { pyodide, loading, error };
};

export default usePyodide;
