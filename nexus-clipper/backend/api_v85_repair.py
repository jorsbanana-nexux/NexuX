
# -- NexuX V9.0: Repair / Self-Heal API Endpoints --

@app.get("/api/repair/diagnose")
async def repair_diagnose(_=Depends(_require_auth)):
    """Run full system diagnostics and return all issues."""
    from engine.repair_system import run_full_diagnosis
    results = run_full_diagnosis()
    return {
        "issues": [
            {"id": r.id, "label": r.label, "status": r.status, "detail": r.detail}
            for r in results
        ],
        "total": len(results),
        "healthy": sum(1 for r in results if r.status == "healthy"),
        "warnings": sum(1 for r in results if r.status == "warning"),
        "errors": sum(1 for r in results if r.status == "error"),
    }


@app.post("/api/repair/fix/{issue_id}")
async def repair_fix_issue(issue_id: str, _=Depends(_require_auth)):
    """Fix a specific issue by ID."""
    from engine.repair_system import fix_issue
    result = fix_issue(issue_id)
    return {
        "id": result.id,
        "label": result.label,
        "status": result.status,
        "detail": result.detail,
    }


@app.post("/api/repair/fix-all")
async def repair_fix_all(_=Depends(_require_auth)):
    """Auto-fix all detected issues."""
    from engine.repair_system import fix_all
    results = fix_all()
    return {
        "fixed": sum(1 for r in results if r.status == "fixed"),
        "results": [
            {"id": r.id, "label": r.label, "status": r.status, "detail": r.detail}
            for r in results
        ],
    }


@app.get("/api/repair/health")
async def repair_health(_=Depends(_require_auth)):
    """Quick health check (4 critical checks only)."""
    from engine.repair_system import quick_health_check
    return quick_health_check()
