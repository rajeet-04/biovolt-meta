def validate_revision(experiment: dict[str, object], revisions: set[str]) -> None:
    revision = experiment.get("calibration_revision_id")
    if not isinstance(revision, str) or revision not in revisions:
        raise ValueError("completed experiment is not pinned to an immutable calibration revision")
