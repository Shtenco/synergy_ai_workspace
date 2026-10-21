import { FormEvent, useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";

type Overview = { product: string; autonomy: string; deployment: string; runtime: string; policy: string; version: string };
type AgentRunResponse = { backend: string; termination: string; stdout: string; stderr: string; duration_ms: number };
type FleetRoleResponse = { role: string; provider: string; model: string; backend: string; success: boolean; summary: string };
type FleetRunResponse = {
  final_state: string; repairs: number; evidence: string[]; role_runs: FleetRoleResponse[]; worktree: string | null;
  writer_runtime: string; review_runtime: string; published: boolean; pull_request: string | null; ci_state: string | null; ci_repairs: number;
};
type MissionView = {
  id: string; objective: string; project: string; state: string; phase: string; attempt: number;
  lease_owner: string | null; lease_until: string | null; checkpoint_phase: string | null;
};
type AgentForm = { backend: string; prompt: string; workdir: string; model: string; allowEnv: string; timeoutMs: string };
type FleetForm = {
  provider: string; model: string; goal: string; repo: string; baseRef: string; profile: string; routes: string;
  allowEnv: string; timeoutMs: string; maxRepairs: string; verifyProgram: string; verifyArgs: string;
  writerRuntime: string; reviewRuntime: string; dockerImage: string; wslDistro: string; publish: boolean; remote: string;
  maxCiRepairs: string; ciPollAttempts: string; ciPollIntervalMs: string;
};

const NAV = ["Command Center", "Goals", "Mission Queue", "Agent Fleet", "Workspace", "Terminal", "Verification", "Models", "MCP & Skills", "Memory", "Policy", "Audit"];
const ROLES = [
  ["DIR", "Director", "Orchestrates the goal graph", "online"], ["ARC", "Architect", "Interfaces and decomposition", "ready"],
  ["COD", "Coder", "Implementation worker", "ready"], ["DBG", "Debugger", "Root-cause and repair", "ready"],
  ["TST", "Tester", "Evidence and regression", "ready"], ["REV", "Reviewer", "Independent cross-review", "ready"],
  ["SEC", "Security", "Policy and risk review", "ready"], ["REL", "Release", "Delivery and release gate", "guarded"],
];
const defaultOverview: Overview = { product: "OPEN AUTOPILOT", autonomy: "Full Autonomy", deployment: "Hybrid local-first", runtime: "Native Windows + WSL2 + Docker", policy: "Secure defaults", version: "0.1.0" };

export default function App() {
  const [overview, setOverview] = useState<Overview>(defaultOverview);
  const [backends, setBackends] = useState<string[]>(["OpenCode", "Codex", "Claude", "Gemini"]);
  const [activeNav, setActiveNav] = useState("Command Center");
  const [mode, setMode] = useState<"agent" | "fleet">("fleet");
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState("Ready for autonomous goal");
  const [agentResult, setAgentResult] = useState<AgentRunResponse | null>(null);
  const [fleetResult, setFleetResult] = useState<FleetRunResponse | null>(null);
  const [missions, setMissions] = useState<MissionView[]>([]);
  const [missionBusy, setMissionBusy] = useState(false);
  const [missionGoal, setMissionGoal] = useState("");
  const [missionProject, setMissionProject] = useState("");
  const [error, setError] = useState("");
  const [agentForm, setAgentForm] = useState<AgentForm>({ backend: "opencode", prompt: "Inspect this repository, identify the highest-impact engineering problem, implement a verified fix, and report the evidence.", workdir: "", model: "", allowEnv: "", timeoutMs: "1800000" });
  const [fleetForm, setFleetForm] = useState<FleetForm>({
    provider: "opencode", model: "", goal: "Analyze this repository, implement the requested change, independently test/review/security-check it, and repair failures until the acceptance command passes.",
    repo: "", baseRef: "main", profile: "best-quality", routes: "", allowEnv: "", timeoutMs: "1800000", maxRepairs: "2",
    verifyProgram: "cargo", verifyArgs: "test,--workspace", writerRuntime: "native", reviewRuntime: "docker", dockerImage: "", wslDistro: "",
    publish: false, remote: "origin", maxCiRepairs: "2", ciPollAttempts: "12", ciPollIntervalMs: "5000",
  });

  useEffect(() => {
    void invoke<Overview>("system_overview").then(setOverview).catch(() => undefined);
    void invoke<string[]>("list_backends").then(setBackends).catch(() => undefined);
    void refreshMissions();
  }, []);

  const missionCounts = useMemo(() => missions.reduce<Record<string, number>>((acc, mission) => {
    acc[mission.state] = (acc[mission.state] ?? 0) + 1;
    return acc;
  }, {}), [missions]);

  const output = useMemo(() => {
    if (error) return error;
    if (mode === "agent") {
      if (!agentResult) return "No direct agent output yet.";
      return [`backend=${agentResult.backend}`, `termination=${agentResult.termination}`, `duration_ms=${agentResult.duration_ms}`, "", agentResult.stdout, agentResult.stderr ? `\n[stderr]\n${agentResult.stderr}` : ""].join("\n");
    }
    if (!fleetResult) return "No fleet run yet. Full Fleet will show role routing, sandbox runtimes, managed worktree, verification evidence and delivery status here.";
    return [
      `final_state=${fleetResult.final_state}`, `repairs=${fleetResult.repairs}`, `worktree=${fleetResult.worktree ?? "n/a"}`,
      `writer_runtime=${fleetResult.writer_runtime}`, `review_runtime=${fleetResult.review_runtime}`, `published=${fleetResult.published}`,
      `pull_request=${fleetResult.pull_request ?? "n/a"}`, `ci_state=${fleetResult.ci_state ?? "n/a"}`, `ci_repairs=${fleetResult.ci_repairs}`, "",
      "[role runs]", ...fleetResult.role_runs.map((run) => `${run.role} -> ${run.provider}/${run.model || "<default>"} (${run.backend}) success=${run.success}\n${run.summary}`),
      "", "[evidence]", ...fleetResult.evidence,
    ].join("\n");
  }, [agentResult, error, fleetResult, mode]);

  function patchAgent<K extends keyof AgentForm>(key: K, value: AgentForm[K]) { setAgentForm((current) => ({ ...current, [key]: value })); }
  function patchFleet<K extends keyof FleetForm>(key: K, value: FleetForm[K]) { setFleetForm((current) => ({ ...current, [key]: value })); }
  function csv(value: string) { return value.split(",").map((item) => item.trim()).filter(Boolean); }
  function routes(value: string) { return value.split(/[\n,]+/).map((item) => item.trim()).filter(Boolean); }

  async function refreshMissions() {
    try { setMissions(await invoke<MissionView[]>("mission_list")); }
    catch (reason) { setError(String(reason)); }
  }

  async function enqueueMission(event: FormEvent) {
    event.preventDefault();
    if (!missionGoal.trim() || !missionProject.trim()) return;
    setMissionBusy(true); setError("");
    try {
      await invoke<MissionView>("mission_enqueue", { goal: missionGoal, project: missionProject });
      setMissionGoal("");
      await refreshMissions();
      setStatus("Mission persisted to durable queue");
    } catch (reason) { setError(String(reason)); }
    finally { setMissionBusy(false); }
  }

  async function recoverMissions() {
    setMissionBusy(true); setError("");
    try {
      const recovered = await invoke<string[]>("mission_recover");
      await refreshMissions();
      setStatus(`Recovered ${recovered.length} expired mission lease(s)`);
    } catch (reason) { setError(String(reason)); }
    finally { setMissionBusy(false); }
  }

  async function cancelMission(id: string) {
    setMissionBusy(true); setError("");
    try {
      await invoke<MissionView>("mission_cancel", { id });
      await refreshMissions();
      setStatus("Mission cancelled; durable history preserved");
    } catch (reason) { setError(String(reason)); }
    finally { setMissionBusy(false); }
  }

  async function runSelected(event: FormEvent) {
    event.preventDefault(); setError(""); setAgentResult(null); setFleetResult(null); setRunning(true);
    setStatus(mode === "fleet" ? "Director is orchestrating the Agent Fleet" : "Agent running under local policy controls");
    try {
      if (mode === "agent") {
        const response = await invoke<AgentRunResponse>("run_agent", { request: {
          backend: agentForm.backend, prompt: agentForm.prompt, workdir: agentForm.workdir, model: agentForm.model.trim() || null,
          allow_env: csv(agentForm.allowEnv), timeout_ms: agentForm.timeoutMs.trim() ? Number(agentForm.timeoutMs) : null,
        }});
        setAgentResult(response); setStatus(response.termination === "Exited" ? "Run completed" : `Run ended: ${response.termination}`);
      } else {
        const response = await invoke<FleetRunResponse>("run_fleet", { request: {
          goal: fleetForm.goal, repo: fleetForm.repo, worktree_root: null, base_ref: fleetForm.baseRef || "main", provider: fleetForm.provider,
          model: fleetForm.model.trim() || null, routes: routes(fleetForm.routes), profile: fleetForm.profile, allow_env: csv(fleetForm.allowEnv),
          timeout_ms: fleetForm.timeoutMs.trim() ? Number(fleetForm.timeoutMs) : null, max_repairs: Number(fleetForm.maxRepairs || 2),
          verify_program: fleetForm.verifyProgram.trim() || null, verify_args: csv(fleetForm.verifyArgs), writer_runtime: fleetForm.writerRuntime,
          review_runtime: fleetForm.reviewRuntime, docker_image: fleetForm.dockerImage.trim() || null, wsl_distro: fleetForm.wslDistro.trim() || null,
          publish: fleetForm.publish, remote: fleetForm.remote || "origin", max_ci_repairs: Number(fleetForm.maxCiRepairs || 2),
          ci_poll_attempts: Number(fleetForm.ciPollAttempts || 12), ci_poll_interval_ms: Number(fleetForm.ciPollIntervalMs || 5000),
        }});
        setFleetResult(response);
        setStatus(response.published ? `Delivered: ${response.ci_state ?? "CI unknown"}` : response.final_state === "Completed" ? "Fleet completed with evidence" : `Fleet ended: ${response.final_state}`);
      }
    } catch (reason) { setError(String(reason)); setStatus("Run failed or was interrupted"); }
    finally { setRunning(false); }
  }

  async function stopAll() {
    setStatus("Emergency stop requested");
    try { setStatus(await invoke<string>("stop_all")); } catch (reason) { setError(String(reason)); }
  }

  const observedRole = (role: string) => fleetResult?.role_runs.find((run) => run.role === role);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">OA</div><div><strong>OPEN AUTOPILOT</strong><span>Autonomous Engineering</span></div></div>
        <nav>{NAV.map((item) => <button key={item} className={activeNav === item ? "nav-item active" : "nav-item"} onClick={() => setActiveNav(item)}><span className="nav-dot" />{item}</button>)}</nav>
        <div className="sidebar-foot"><span className="pulse" /> Local control plane<small>v{overview.version}</small></div>
      </aside>

      <main className="main-panel">
        <header className="topbar"><div><div className="eyebrow">{activeNav}</div><h1>Autonomous Command Center</h1></div><div className="top-actions"><div className="mode-pill"><span className="pulse" /> {overview.autonomy}</div><button className="stop-button" onClick={() => void stopAll()}>STOP</button></div></header>
        <section className="status-grid">
          <StatusCard label="DIRECTOR" value="ONLINE" detail="DAG orchestration + bounded repair" accent="green" />
          <StatusCard label="MISSIONS" value={`${missionCounts.Queued ?? 0} QUEUED`} detail={`${missionCounts.Running ?? 0} running · ${missionCounts.Waiting ?? 0} waiting`} />
          <StatusCard label="POLICY GUARD" value="ENFORCED" detail={overview.policy} accent="green" />
          <StatusCard label="RUNTIME" value={overview.runtime} detail="Durable state + role isolation + shared STOP" />
        </section>

        {activeNav === "Mission Queue" ? (
          <section className="card mission-board">
            <div className="card-heading"><div><div className="eyebrow">DURABLE MISSION QUEUE</div><h2>Persistent work survives process and Windows restarts</h2></div><div className="mission-actions"><button className="nav-item" disabled={missionBusy} onClick={() => void refreshMissions()}>REFRESH</button><button className="nav-item" disabled={missionBusy} onClick={() => void recoverMissions()}>RECOVER EXPIRED</button></div></div>
            <form className="mission-compose" onSubmit={(event) => void enqueueMission(event)}>
              <label>Mission objective<textarea value={missionGoal} onChange={(event) => setMissionGoal(event.target.value)} rows={3} placeholder="Fix checkout, verify, publish PR and keep CI green" required /></label>
              <label>Project directory<input value={missionProject} onChange={(event) => setMissionProject(event.target.value)} placeholder="C:\\dev\\project" required /></label>
              <button className="primary-button" disabled={missionBusy} type="submit">ENQUEUE DURABLY</button>
            </form>
            <div className="mission-grid">
              {missions.length === 0 ? <div className="empty-state">No durable missions yet.</div> : missions.map((mission) => (
                <article className="mission-card" key={mission.id}>
                  <div className="mission-head"><span className={`mission-state state-${mission.state.toLowerCase()}`}>{mission.state}</span><code>{mission.id.slice(0, 8)}</code></div>
                  <strong>{mission.objective}</strong>
                  <span className="mission-project">{mission.project}</span>
                  <div className="mission-meta"><span>attempt {mission.attempt}</span><span>phase {mission.phase}</span><span>checkpoint {mission.checkpoint_phase ?? "none"}</span></div>
                  {mission.lease_owner && <div className="mission-lease">lease: {mission.lease_owner} · {mission.lease_until ?? "no deadline"}</div>}
                  {!['Completed','Failed','Cancelled'].includes(mission.state) && <button className="stop-button mission-cancel" disabled={missionBusy} onClick={() => void cancelMission(mission.id)}>CANCEL</button>}
                </article>
              ))}
            </div>
          </section>
        ) : (
          <>
            <section className="workspace-grid">
              <div className="card launch-card">
                <div className="card-heading"><div><div className="eyebrow">GOAL LAUNCHER</div><h2>{mode === "fleet" ? "Launch the autonomous Agent Fleet" : "Run one coding agent"}</h2></div><div className={running ? "run-indicator running" : "run-indicator"}>{running ? "RUNNING" : "READY"}</div></div>
                <div className="field-row"><button type="button" className={mode === "fleet" ? "primary-button" : "nav-item"} onClick={() => setMode("fleet")}>FULL FLEET</button><button type="button" className={mode === "agent" ? "primary-button" : "nav-item"} onClick={() => setMode("agent")}>SINGLE AGENT</button></div>
                <form onSubmit={(event) => void runSelected(event)}>
                  {mode === "agent" ? <>
                    <div className="field-row"><label>Backend<select value={agentForm.backend} onChange={(e) => patchAgent("backend", e.target.value)}>{backends.map((backend) => <option value={backend.toLowerCase().replace(" ", "-")} key={backend}>{backend}</option>)}</select></label><label>Model override<input value={agentForm.model} onChange={(e) => patchAgent("model", e.target.value)} placeholder="Auto / provider default" /></label></div>
                    <label>Repository / work directory<input value={agentForm.workdir} onChange={(e) => patchAgent("workdir", e.target.value)} placeholder="C:\\dev\\my-project" required /></label>
                    <label>Objective<textarea value={agentForm.prompt} onChange={(e) => patchAgent("prompt", e.target.value)} rows={6} required /></label>
                    <div className="field-row"><label>Explicit environment allowlist<input value={agentForm.allowEnv} onChange={(e) => patchAgent("allowEnv", e.target.value)} placeholder="OPENAI_API_KEY, GH_TOKEN" /></label><label>Timeout (ms)<input value={agentForm.timeoutMs} onChange={(e) => patchAgent("timeoutMs", e.target.value)} inputMode="numeric" /></label></div>
                  </> : <>
                    <div className="field-row"><label>Default provider<select value={fleetForm.provider} onChange={(e) => patchFleet("provider", e.target.value)}><option value="opencode">OpenCode</option><option value="openai">Codex / OpenAI</option><option value="anthropic">Claude</option><option value="google">Gemini</option></select></label><label>Default model override<input value={fleetForm.model} onChange={(e) => patchFleet("model", e.target.value)} placeholder="Provider default" /></label></div>
                    <label>Repository<input value={fleetForm.repo} onChange={(e) => patchFleet("repo", e.target.value)} placeholder="C:\\dev\\my-project" required /></label>
                    <label>Goal<textarea value={fleetForm.goal} onChange={(e) => patchFleet("goal", e.target.value)} rows={5} required /></label>
                    <label>Role routing overrides<textarea value={fleetForm.routes} onChange={(e) => patchFleet("routes", e.target.value)} rows={3} placeholder={"architect=anthropic:MODEL\ncoder=openai:MODEL\ntester=google:MODEL\nreviewer=anthropic:MODEL"} /></label>
                    <div className="field-row"><label>Writer runtime<select value={fleetForm.writerRuntime} onChange={(e) => patchFleet("writerRuntime", e.target.value)}><option value="native">Native Windows</option><option value="wsl">WSL2</option><option value="docker">Docker</option></select></label><label>Review runtime<select value={fleetForm.reviewRuntime} onChange={(e) => patchFleet("reviewRuntime", e.target.value)}><option value="docker">Docker hard read-only</option><option value="native">Native (will fail closed)</option><option value="wsl">WSL2 (will fail closed)</option></select></label></div>
                    <div className="field-row"><label>Docker image<input value={fleetForm.dockerImage} onChange={(e) => patchFleet("dockerImage", e.target.value)} placeholder="Image with selected agent CLI" /></label><label>WSL distribution<input value={fleetForm.wslDistro} onChange={(e) => patchFleet("wslDistro", e.target.value)} placeholder="Ubuntu" /></label></div>
                    <div className="field-row"><label>Routing profile<select value={fleetForm.profile} onChange={(e) => patchFleet("profile", e.target.value)}><option value="best-quality">Best Quality</option><option value="balanced">Balanced</option><option value="budget">Budget</option></select></label><label>Base ref<input value={fleetForm.baseRef} onChange={(e) => patchFleet("baseRef", e.target.value)} /></label></div>
                    <div className="field-row"><label>Acceptance program<input value={fleetForm.verifyProgram} onChange={(e) => patchFleet("verifyProgram", e.target.value)} placeholder="cargo" /></label><label>Acceptance args<input value={fleetForm.verifyArgs} onChange={(e) => patchFleet("verifyArgs", e.target.value)} placeholder="test,--workspace" /></label></div>
                    <div className="field-row"><label>Environment allowlist<input value={fleetForm.allowEnv} onChange={(e) => patchFleet("allowEnv", e.target.value)} placeholder="OPENAI_API_KEY, GH_TOKEN" /></label><label>Repair budget / timeout<div className="field-row"><input value={fleetForm.maxRepairs} onChange={(e) => patchFleet("maxRepairs", e.target.value)} inputMode="numeric" /><input value={fleetForm.timeoutMs} onChange={(e) => patchFleet("timeoutMs", e.target.value)} inputMode="numeric" /></div></label></div>
                    <div className="delivery-panel">
                      <label className="publish-toggle"><input type="checkbox" checked={fleetForm.publish} onChange={(e) => patchFleet("publish", e.target.checked)} /> Publish verified result to GitHub PR and repair CI automatically</label>
                      <div className="field-row"><label>Git remote<input value={fleetForm.remote} onChange={(e) => patchFleet("remote", e.target.value)} /></label><label>Max CI repairs<input value={fleetForm.maxCiRepairs} onChange={(e) => patchFleet("maxCiRepairs", e.target.value)} inputMode="numeric" /></label></div>
                      <div className="field-row"><label>CI poll attempts<input value={fleetForm.ciPollAttempts} onChange={(e) => patchFleet("ciPollAttempts", e.target.value)} inputMode="numeric" /></label><label>CI poll interval ms<input value={fleetForm.ciPollIntervalMs} onChange={(e) => patchFleet("ciPollIntervalMs", e.target.value)} inputMode="numeric" /></label></div>
                    </div>
                  </>}
                  <div className="form-footer"><div className="status-copy"><span className={running ? "pulse hot" : "pulse"} /> {status}</div><button className="primary-button" type="submit" disabled={running}>{running ? "AUTOPILOT IS WORKING…" : mode === "fleet" ? "RUN FULL AUTOPILOT" : "RUN AGENT"}</button></div>
                </form>
              </div>
              <div className="card terminal-card"><div className="card-heading compact"><div><div className="eyebrow">EXECUTION OUTPUT</div><h2>Autopilot console</h2></div><span className="terminal-badge">LOCAL</span></div><pre>{output}</pre></div>
            </section>

            {fleetResult && <section className="delivery-strip">
              <span className="runtime-badge">WRITE: {fleetResult.writer_runtime}</span><span className="runtime-badge">REVIEW: {fleetResult.review_runtime}</span>
              <span className={fleetResult.published ? "runtime-badge good" : "runtime-badge"}>PR: {fleetResult.published ? "PUBLISHED" : "LOCAL ONLY"}</span>
              {fleetResult.ci_state && <span className={fleetResult.ci_state === "Passing" ? "runtime-badge good" : "runtime-badge warn"}>CI: {fleetResult.ci_state}</span>}
              {fleetResult.pull_request && <span className="runtime-badge">{fleetResult.pull_request}</span>}
            </section>}

            <section className="card fleet-card"><div className="card-heading"><div><div className="eyebrow">AGENT FLEET</div><h2>Director + specialist workers</h2></div><span className="subtle">Architect → Coder → parallel Tester / Reviewer / Security → Debugger repair → PR/CI</span></div><div className="fleet-grid">{ROLES.map(([code, role, detail, roleStatus]) => { const observed = observedRole(role); const statusLabel = observed ? (observed.success ? "passed" : "failed") : roleStatus; return <article className="agent-card" key={role}><div className="agent-avatar">{code}</div><div className="agent-copy"><strong>{role}</strong><span>{observed ? `${observed.provider}/${observed.model || "default"}` : detail}</span></div><span className={`agent-status ${statusLabel}`}>{statusLabel}</span></article>; })}</div></section>
          </>
        )}
      </main>
    </div>
  );
}

function StatusCard({ label, value, detail, accent }: { label: string; value: string; detail: string; accent?: "green" }) {
  return <article className="status-card"><span className="eyebrow">{label}</span><strong className={accent === "green" ? "green" : ""}>{value}</strong><small>{detail}</small></article>;
}
