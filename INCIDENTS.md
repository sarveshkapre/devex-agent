# Incidents

## Incident 2026-02-09 - CI quality gate failed on all pushes
- Status: Resolved
- Severity: Medium
- Detection:
  - GitHub Actions `ci` workflow failures on `main` (for example runs `21557668393`, `21557634924`).
- Impact:
  - All `build` jobs failed at `make check`, blocking confidence in release quality and hiding downstream audit results.
- Root Cause:
  - `Makefile` targets assumed a local virtualenv and executed `. .venv/bin/activate` in every command.
  - CI job installs dependencies globally and does not create `.venv`, so shell activation failed immediately.
- Resolution:
  - Updated `Makefile` to use `.venv/bin/*` tools only when `.venv` exists, otherwise use `PATH` tools.
  - Verified with:
    - `make check`
    - `PATH="$(pwd)/.venv/bin:$PATH" make check VENV=.missing`
    - GitHub Actions run `21808754489` (success)
- Prevention Rules:
  - Build and test commands must not assume local shell activation state.
  - Verify any build-tooling change in both local-venv and CI-like execution modes.
  - Keep a CI smoke run check after each push that changes automation or developer tooling.

### 2026-02-12T20:01:33Z | Codex execution failure
- Date: 2026-02-12T20:01:33Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-2.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:05:01Z | Codex execution failure
- Date: 2026-02-12T20:05:01Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-3.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:08:31Z | Codex execution failure
- Date: 2026-02-12T20:08:31Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-4.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:11:58Z | Codex execution failure
- Date: 2026-02-12T20:11:58Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-5.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:15:28Z | Codex execution failure
- Date: 2026-02-12T20:15:28Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-6.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:18:58Z | Codex execution failure
- Date: 2026-02-12T20:18:58Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-7.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:22:23Z | Codex execution failure
- Date: 2026-02-12T20:22:23Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-8.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:25:54Z | Codex execution failure
- Date: 2026-02-12T20:25:54Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-9.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:29:34Z | Codex execution failure
- Date: 2026-02-12T20:29:34Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-10.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:33:01Z | Codex execution failure
- Date: 2026-02-12T20:33:01Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-11.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:36:31Z | Codex execution failure
- Date: 2026-02-12T20:36:31Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-12.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:39:58Z | Codex execution failure
- Date: 2026-02-12T20:39:58Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-13.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:43:26Z | Codex execution failure
- Date: 2026-02-12T20:43:26Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-14.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:47:00Z | Codex execution failure
- Date: 2026-02-12T20:47:00Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-15.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:50:29Z | Codex execution failure
- Date: 2026-02-12T20:50:29Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-devex-agent-cycle-16.log
- Commit: pending
- Confidence: medium
