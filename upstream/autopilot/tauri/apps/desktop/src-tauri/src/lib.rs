mod missions;

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::Duration;

use autopilot_audit::InMemoryAuditStore;
use autopilot_delivery::{CiReport, CiState, DeliveryConfig, DeliveryEngine};
use autopilot_domain::{AgentRole, GoalState};
use autopilot_engine::{backend_for_provider, FleetEngine, FleetEngineConfig, VerificationCommand};
use autopilot_harness::{AgentHarness, BackendKind, BackendRegistry, RunSpec, Termination};
use autopilot_router::{ModelCandidate, ModelRouter, RoutingProfile};
use autopilot_runtime::{CommandSpec, DockerRuntime, ExecutionProfile, NativeRuntime, RuntimeAdapter, WslRuntime};
use serde::{Deserialize, Serialize};
use tauri::State;

#[derive(Clone)]
struct AppState { runtime: NativeRuntime }

#[derive(Serialize)]
struct SystemOverview {
    product: &'static str,
    autonomy: &'static str,
    deployment: &'static str,
    runtime: &'static str,
    policy: &'static str,
    version: &'static str,
}

#[derive(Debug, Deserialize)]
struct AgentRunRequest {
    backend: String,
    prompt: String,
    workdir: String,
    model: Option<String>,
    #[serde(default)] allow_env: Vec<String>,
    timeout_ms: Option<u64>,
}

#[derive(Serialize)]
struct AgentRunResponse {
    backend: String,
    termination: String,
    stdout: String,
    stderr: String,
    duration_ms: u128,
}

#[derive(Debug, Deserialize)]
struct FleetRunRequest {
    goal: String,
    repo: String,
    worktree_root: Option<String>,
    base_ref: Option<String>,
    provider: Option<String>,
    model: Option<String>,
    #[serde(default)] routes: Vec<String>,
    profile: Option<String>,
    #[serde(default)] allow_env: Vec<String>,
    timeout_ms: Option<u64>,
    max_repairs: Option<usize>,
    verify_program: Option<String>,
    #[serde(default)] verify_args: Vec<String>,
    writer_runtime: Option<String>,
    review_runtime: Option<String>,
    docker_image: Option<String>,
    wsl_distro: Option<String>,
    publish: Option<bool>,
    remote: Option<String>,
    max_ci_repairs: Option<usize>,
    ci_poll_attempts: Option<usize>,
    ci_poll_interval_ms: Option<u64>,
}

#[derive(Serialize)]
struct FleetRoleResponse {
    role: String,
    provider: String,
    model: String,
    backend: String,
    success: bool,
    summary: String,
}

#[derive(Serialize)]
struct FleetRunResponse {
    final_state: String,
    repairs: usize,
    evidence: Vec<String>,
    role_runs: Vec<FleetRoleResponse>,
    worktree: Option<String>,
    writer_runtime: String,
    review_runtime: String,
    published: bool,
    pull_request: Option<String>,
    ci_state: Option<String>,
    ci_repairs: usize,
}

fn backend_from_name(name: &str) -> Result<BackendKind, String> {
    match name.trim().to_ascii_lowercase().as_str() {
        "opencode" => Ok(BackendKind::OpenCode),
        "codex" => Ok(BackendKind::Codex),
        "claude" | "claude-code" => Ok(BackendKind::Claude),
        "gemini" => Ok(BackendKind::Gemini),
        other => Err(format!("unsupported builtin backend: {other}")),
    }
}

fn parse_role(value: &str) -> Result<AgentRole, String> {
    match value.trim().to_ascii_lowercase().as_str() {
        "architect" => Ok(AgentRole::Architect),
        "coder" => Ok(AgentRole::Coder),
        "tester" => Ok(AgentRole::Tester),
        "reviewer" => Ok(AgentRole::Reviewer),
        "security" => Ok(AgentRole::Security),
        "debugger" => Ok(AgentRole::Debugger),
        other => Err(format!("unsupported fleet role: {other}")),
    }
}

fn parse_profile(value: Option<&str>) -> Result<RoutingProfile, String> {
    match value.unwrap_or("best-quality").trim().to_ascii_lowercase().as_str() {
        "best" | "best-quality" | "quality" => Ok(RoutingProfile::BestQuality),
        "balanced" => Ok(RoutingProfile::Balanced),
        "budget" => Ok(RoutingProfile::Budget),
        other => Err(format!("unsupported routing profile: {other}")),
    }
}

fn parse_route(value: &str) -> Result<(AgentRole, String, String), String> {
    let (role, target) = value.split_once('=').ok_or_else(|| format!("route must use role=provider[:model], got: {value}"))?;
    let role = parse_role(role)?;
    let (provider, model) = match target.split_once(':') {
        Some((provider, model)) => (provider.to_string(), model.to_string()),
        None => (target.to_string(), String::new()),
    };
    if provider.trim().is_empty() { return Err(format!("route provider is empty: {value}")); }
    Ok((role, provider, model))
}

fn candidate(provider: String, model: String, role: AgentRole) -> ModelCandidate {
    let mut affinities = BTreeMap::new();
    affinities.insert(role, 100);
    ModelCandidate { provider, model, quality: 90, cost_per_million: 1.0, latency_ms: 500, healthy: true, role_affinities: affinities }
}

fn fleet_candidates(default_provider: String, default_model: Option<String>, routes: Vec<String>) -> Result<Vec<ModelCandidate>, String> {
    let mut overrides = BTreeMap::new();
    for route in routes {
        let (role, provider, model) = parse_route(&route)?;
        overrides.insert(role, (provider, model));
    }
    let default_model = default_model.unwrap_or_default();
    Ok([
        AgentRole::Architect, AgentRole::Coder, AgentRole::Tester,
        AgentRole::Reviewer, AgentRole::Security, AgentRole::Debugger,
    ].into_iter().map(|role| {
        let (provider, model) = overrides.get(&role).cloned().unwrap_or_else(|| (default_provider.clone(), default_model.clone()));
        candidate(provider, model, role)
    }).collect())
}

fn build_runtime(kind: &str, workspace: &Path, docker_image: Option<&str>, wsl_distro: Option<&str>, shared_native: NativeRuntime) -> Result<Arc<dyn RuntimeAdapter>, String> {
    match kind.trim().to_ascii_lowercase().as_str() {
        "native" | "windows" => Ok(Arc::new(shared_native)),
        "wsl" | "wsl2" => Ok(Arc::new(WslRuntime::with_native(shared_native, wsl_distro.map(str::to_string)))),
        "docker" => {
            let image = docker_image.filter(|value| !value.trim().is_empty())
                .ok_or_else(|| "Docker runtime requires a non-empty docker_image containing the selected coding-agent CLI".to_string())?;
            Ok(Arc::new(DockerRuntime::with_native(shared_native, image, workspace.to_path_buf())))
        }
        other => Err(format!("unsupported runtime: {other}; expected native, wsl, or docker")),
    }
}

async fn current_branch(runtime: Arc<dyn RuntimeAdapter>, worktree: &Path) -> Result<String, String> {
    let result = runtime.execute(
        CommandSpec::new("git").args(["branch", "--show-current"])
            .cwd(worktree.to_path_buf()).profile(ExecutionProfile::WorkspaceWrite)
    ).await.map_err(|error| error.to_string())?;
    if result.exit_code != 0 { return Err(format!("cannot resolve delivery branch: {}", result.stderr)); }
    let branch = result.stdout.trim().to_string();
    if branch.is_empty() { return Err("delivery worktree is detached; refusing autonomous push".into()); }
    Ok(branch)
}

async fn run_acceptance(runtime: Arc<dyn RuntimeAdapter>, worktree: &Path, checks: &[VerificationCommand]) -> Result<bool, String> {
    for check in checks {
        let result = runtime.execute(
            CommandSpec::new(check.program.clone()).args(check.args.clone())
                .cwd(worktree.to_path_buf()).profile(ExecutionProfile::WorkspaceWrite)
        ).await.map_err(|error| error.to_string())?;
        if result.exit_code != 0 { return Ok(false); }
    }
    Ok(true)
}

async fn wait_for_ci(engine: &DeliveryEngine, attempts: usize, interval_ms: u64) -> Result<CiReport, String> {
    let mut last = engine.read_ci().await.map_err(|error| error.to_string())?;
    for _ in 1..attempts.max(1) {
        if last.state != CiState::Pending { return Ok(last); }
        tokio::time::sleep(Duration::from_millis(interval_ms)).await;
        last = engine.read_ci().await.map_err(|error| error.to_string())?;
    }
    Ok(last)
}

async fn repair_failing_ci(
    runtime: Arc<dyn RuntimeAdapter>, worktree: &Path, goal: &str,
    candidates: &[ModelCandidate], routing_profile: RoutingProfile,
    allowed_env: &[String], timeout_ms: Option<u64>, report: &CiReport,
) -> Result<(), String> {
    let candidate = ModelRouter::select(&AgentRole::Debugger, routing_profile, candidates)
        .ok_or_else(|| "no healthy Debugger model available for CI repair".to_string())?;
    let backend = backend_for_provider(&candidate.provider)?;
    let failures = report.checks.iter().filter(|check| {
        let bucket = check.bucket.to_ascii_lowercase();
        let state = check.state.to_ascii_lowercase();
        bucket == "fail" || state.contains("fail") || state.contains("error") || state.contains("cancel")
    }).map(|check| format!("{} [{}] {}", check.name, check.state, check.link)).collect::<Vec<_>>().join("\n");
    let prompt = format!("Act as the Debugger. GitHub CI failed after a locally verified change. Goal: {goal}\nFailing checks:\n{failures}\nDiagnose and make the minimum corrective edits in this worktree. Do not force-push, publish releases, or expose secrets.");
    let mut spec = RunSpec::new(backend, prompt, worktree.to_path_buf())
        .model(candidate.model).profile(ExecutionProfile::WorkspaceWrite);
    for key in allowed_env { spec = spec.allow_env(key.clone()); }
    if let Some(timeout) = timeout_ms { spec = spec.timeout_ms(timeout); }
    let result = AgentHarness::new(runtime, BackendRegistry::default())
        .run(spec).await.map_err(|error| error.to_string())?;
    if !matches!(result.termination, Termination::Exited) {
        return Err(format!("CI Debugger failed: {:?}: {}", result.termination, result.stderr));
    }
    Ok(())
}

#[tauri::command]
fn system_overview() -> SystemOverview {
    SystemOverview {
        product: "OPEN AUTOPILOT",
        autonomy: "Full Autonomy",
        deployment: "Hybrid local-first",
        runtime: "Native Windows + WSL2 + Docker",
        policy: "Hard read-only review via Docker; durable missions; no force-push; publish is explicit opt-in",
        version: env!("CARGO_PKG_VERSION"),
    }
}

#[tauri::command]
fn list_backends() -> Vec<&'static str> { vec!["OpenCode", "Codex", "Claude", "Gemini"] }

#[tauri::command]
async fn run_agent(request: AgentRunRequest, state: State<'_, AppState>) -> Result<AgentRunResponse, String> {
    if request.workdir.trim().is_empty() { return Err("workdir cannot be empty".into()); }
    if request.prompt.trim().is_empty() { return Err("prompt cannot be empty".into()); }
    let backend = backend_from_name(&request.backend)?;
    let mut spec = RunSpec::new(backend, request.prompt, request.workdir.into());
    if let Some(model) = request.model.filter(|value| !value.trim().is_empty()) { spec = spec.model(model); }
    for key in request.allow_env.into_iter().filter(|key| !key.trim().is_empty()) { spec = spec.allow_env(key); }
    if let Some(timeout_ms) = request.timeout_ms { spec = spec.timeout_ms(timeout_ms); }
    let result = AgentHarness::new(Arc::new(state.runtime.clone()), BackendRegistry::default())
        .run(spec).await.map_err(|error| error.to_string())?;
    let termination = match result.termination {
        Termination::Exited => "Exited".to_string(),
        Termination::NonZero(code) => format!("NonZero({code})"),
    };
    Ok(AgentRunResponse { backend: format!("{:?}", result.backend), termination, stdout: result.stdout, stderr: result.stderr, duration_ms: result.duration_ms })
}

#[tauri::command]
async fn run_fleet(request: FleetRunRequest, state: State<'_, AppState>) -> Result<FleetRunResponse, String> {
    if request.goal.trim().is_empty() { return Err("goal cannot be empty".into()); }
    if request.repo.trim().is_empty() { return Err("repo cannot be empty".into()); }

    let repo = PathBuf::from(request.repo);
    let goal = request.goal;
    let base_ref = request.base_ref.unwrap_or_else(|| "main".into());
    let routing_profile = parse_profile(request.profile.as_deref())?;
    let worktree_root = request.worktree_root.map(PathBuf::from)
        .unwrap_or_else(|| repo.join(".open-autopilot").join("worktrees"));
    let verification = request.verify_program.filter(|program| !program.trim().is_empty())
        .map(|program| vec![VerificationCommand::new("acceptance", program, request.verify_args)])
        .unwrap_or_default();
    let publish = request.publish.unwrap_or(false);
    if publish && verification.is_empty() {
        return Err("Publish requires a verification command so delivery has local acceptance evidence".into());
    }
    let candidates = fleet_candidates(request.provider.unwrap_or_else(|| "opencode".into()), request.model, request.routes)?;
    let writer_runtime_name = request.writer_runtime.unwrap_or_else(|| "native".into());
    let review_runtime_name = request.review_runtime.unwrap_or_else(|| "docker".into());
    let writer_runtime = build_runtime(&writer_runtime_name, &repo, request.docker_image.as_deref(), request.wsl_distro.as_deref(), state.runtime.clone())?;
    let review_runtime = build_runtime(&review_runtime_name, &repo, request.docker_image.as_deref(), request.wsl_distro.as_deref(), state.runtime.clone())?;
    if !writer_runtime.probe().await { return Err(format!("writer runtime `{writer_runtime_name}` is unavailable")); }
    if !review_runtime.probe().await { return Err(format!("review runtime `{review_runtime_name}` is unavailable")); }

    let allowed_env = request.allow_env;
    let timeout_ms = request.timeout_ms;
    let audit = Arc::new(InMemoryAuditStore::default());
    let engine = FleetEngine::with_role_runtimes(
        writer_runtime.clone(), review_runtime, audit,
        FleetEngineConfig {
            repo_root: repo.clone(), worktree_root, base_ref: base_ref.clone(), routing_profile,
            candidates: candidates.clone(), allowed_env: allowed_env.clone(), timeout_ms,
            verification: verification.clone(), max_repairs: request.max_repairs.unwrap_or(2),
        },
    );
    let summary = engine.run(goal.clone()).await?;

    let mut response = FleetRunResponse {
        final_state: format!("{:?}", summary.final_state),
        repairs: summary.repairs,
        evidence: summary.evidence.iter().map(|item| format!("{}:{}:{}", item.kind, item.passed, item.summary)).collect(),
        role_runs: summary.role_runs.iter().map(|run| FleetRoleResponse {
            role: format!("{:?}", run.role), provider: run.provider.clone(), model: run.model.clone(),
            backend: format!("{:?}", run.backend), success: run.success, summary: run.summary.clone(),
        }).collect(),
        worktree: summary.worktree.as_ref().map(|path| path.to_string_lossy().into_owned()),
        writer_runtime: writer_runtime_name,
        review_runtime: review_runtime_name,
        published: false,
        pull_request: None,
        ci_state: None,
        ci_repairs: 0,
    };

    if !publish { return Ok(response); }
    if summary.final_state != GoalState::Completed {
        return Err("refusing publish because local fleet verification did not complete successfully".into());
    }
    let worktree = summary.worktree.ok_or_else(|| "verified fleet result has no worktree".to_string())?;
    let branch = current_branch(writer_runtime.clone(), &worktree).await?;
    let delivery = DeliveryEngine::new(writer_runtime.clone(), DeliveryConfig {
        workdir: worktree.clone(),
        remote: request.remote.unwrap_or_else(|| "origin".into()),
        branch,
        base: base_ref,
        title: format!("OPEN AUTOPILOT: {}", goal.chars().take(72).collect::<String>()),
        body: "Automated change produced by OPEN AUTOPILOT. Local verification, independent review and policy gates completed before publication.".into(),
    }).map_err(|error| error.to_string())?;
    let pr = delivery.publish_verified_change("feat: OPEN AUTOPILOT verified change")
        .await.map_err(|error| error.to_string())?;
    response.published = true;
    response.pull_request = Some(pr.url);

    let max_ci_repairs = request.max_ci_repairs.unwrap_or(2);
    let mut ci_repairs = 0usize;
    loop {
        let report = wait_for_ci(&delivery, request.ci_poll_attempts.unwrap_or(12), request.ci_poll_interval_ms.unwrap_or(5_000)).await?;
        response.ci_state = Some(format!("{:?}", report.state));
        match report.state {
            CiState::Passing => break,
            CiState::Pending => return Err("CI remained pending after the configured polling budget".into()),
            CiState::Unknown => return Err("CI state is unknown; refusing to claim delivery success".into()),
            CiState::Failing if ci_repairs < max_ci_repairs => {
                ci_repairs += 1;
                repair_failing_ci(writer_runtime.clone(), &worktree, &goal, &candidates, routing_profile, &allowed_env, timeout_ms, &report).await?;
                if !run_acceptance(writer_runtime.clone(), &worktree, &verification).await? {
                    return Err("CI Debugger changed the worktree but local acceptance verification still fails".into());
                }
                delivery.prepare_commit(&format!("fix: repair CI attempt {ci_repairs}"))
                    .await.map_err(|error| error.to_string())?;
                delivery.push_branch().await.map_err(|error| error.to_string())?;
                response.ci_repairs = ci_repairs;
            }
            CiState::Failing => return Err(format!("CI remains failing after {max_ci_repairs} repair attempts")),
        }
    }
    Ok(response)
}

#[tauri::command]
async fn stop_all(state: State<'_, AppState>) -> Result<String, String> {
    state.runtime.cancel().await.map_err(|error| error.to_string())?;
    Ok("Emergency stop sent to active Native/WSL/Docker execution; durable mission state preserved".into())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mission_state = missions::init_state().expect("failed to initialize OPEN AUTOPILOT state.db");
    tauri::Builder::default()
        .manage(AppState { runtime: NativeRuntime::default() })
        .manage(mission_state)
        .invoke_handler(tauri::generate_handler![
            system_overview,
            list_backends,
            run_agent,
            run_fleet,
            stop_all,
            missions::mission_enqueue,
            missions::mission_list,
            missions::mission_recover,
            missions::mission_cancel
        ])
        .run(tauri::generate_context!())
        .expect("error while running OPEN AUTOPILOT desktop");
}
