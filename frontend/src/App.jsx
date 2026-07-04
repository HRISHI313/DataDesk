import { useState } from "react";
import TaskLauncher from "./components/TaskLauncher/TaskLauncher";
import Analyser from "./components/Analyser/Analyser";
import "./App.css";

function App() {
  const [tab, setTab] = useState("analyser");

  return (
    <div className="app-shell">
      <nav className="app-tabs">
        <button
          className={tab === "analyser" ? "app-tab active" : "app-tab"}
          onClick={() => setTab("analyser")}
        >
          Analyser
        </button>
        <button
          className={tab === "task-launcher" ? "app-tab active" : "app-tab"}
          onClick={() => setTab("task-launcher")}
        >
          Task Launcher
        </button>
      </nav>

      {tab === "analyser" && <Analyser />}
      {tab === "task-launcher" && <TaskLauncher />}
    </div>
  );
}

export default App;
