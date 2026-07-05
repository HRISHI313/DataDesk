import { useState } from "react";
import TaskLauncher from "./components/TaskLauncher/TaskLauncher";
import Analyser from "./components/Analyser/Analyser";
import "./App.css";

function App() {
  const [tab, setTab] = useState("analyser");

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="app-wordmark">
          <span className="wordmark-dot" />
          DataDesk
        </div>
        <nav className="app-nav">
          <button
            className={tab === "analyser" ? "app-nav-item active" : "app-nav-item"}
            onClick={() => setTab("analyser")}
          >
            <span className="status-dot verified" />
            Analyser
          </button>
          <button
            className={tab === "task-launcher" ? "app-nav-item active" : "app-nav-item"}
            onClick={() => setTab("task-launcher")}
          >
            <span className="status-dot pending" />
            Task Launcher
          </button>
        </nav>
      </aside>

      <main className="app-main">
        {tab === "analyser" && <Analyser />}
        {tab === "task-launcher" && <TaskLauncher />}
      </main>
    </div>
  );
}

export default App;
