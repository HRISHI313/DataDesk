import { useState } from "react";
import TaskLauncher from "./components/TaskLauncher/TaskLauncher";
import Analyser from "./components/Analyser/Analyser";
import "./App.css";

function App() {
  const [tab, setTab] = useState("analyser");
  const [taskLauncherPreload, setTaskLauncherPreload] = useState(null);

  function handleLaunchTask(taskData) {
    setTaskLauncherPreload(taskData);
    setTab("task-launcher");
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="app-wordmark">
          <span className="wordmark-dot" />
          DataDesk
          <span style={{
          fontSize: '10px',
          fontWeight: 700,
          color: 'var(--accent)',
          background: 'rgba(76, 141, 255, 0.15)',
          padding: '2px 6px',
          borderRadius: '4px',
          marginLeft: '4px'
  }}>V2.0</span>
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
        {tab === "analyser" && <Analyser onLaunchTask={handleLaunchTask} />}
        {tab === "task-launcher" && (
          <TaskLauncher
            initialData={taskLauncherPreload}
            onInitialDataConsumed={() => setTaskLauncherPreload(null)}
          />
        )}
      </main>
    </div>
  );
}

export default App;
