from datetime import datetime, timedelta
from typing import Optional, Tuple

from neofinesse.reconciliation.candidates import CandidateEvent
from neofinesse.models.settlement import Settlement


class TemporalStatus:
    VALID_TEMPORAL_RELATIONSHIP = "VALID_TEMPORAL_RELATIONSHIP"
    OUTSIDE_WINDOW = "OUTSIDE_WINDOW"
    INSUFFICIENT_TIMING_EVIDENCE = "INSUFFICIENT_TIMING_EVIDENCE"


class TemporalConstraintFilter:
    """Applies temporal cutoff and sequencing constraints to candidate financial events."""

    def __init__(self, allowable_lead_buffer_hours: float = 2.0):
        self.allowable_lead_buffer_hours = allowable_lead_buffer_hours

    def validate_candidate_timing(
        self, candidate: CandidateEvent, settlement: Settlement
    ) -> Tuple[bool, str, str]:
        """Validates whether candidate event timestamp precedes the settlement batch cutoff."""
        if not candidate.timestamp:
            return (
                False,
                TemporalStatus.INSUFFICIENT_TIMING_EVIDENCE,
                "Candidate event lacks a verifiable timestamp.",
            )

        settle_time = settlement.settled_at or settlement.created_at
        if not settle_time:
            return (
                False,
                TemporalStatus.INSUFFICIENT_TIMING_EVIDENCE,
                "Target settlement lacks a verifiable creation/settled timestamp.",
            )

        # The candidate event must have occurred BEFORE the settlement was created / processed
        # Allow a tiny grace buffer for network clock skew
        max_allowed_time = settle_time + timedelta(hours=self.allowable_lead_buffer_hours)

        if candidate.timestamp <= max_allowed_time:
            return (
                True,
                TemporalStatus.VALID_TEMPORAL_RELATIONSHIP,
                f"Candidate timestamp {candidate.timestamp.isoformat()} precedes settlement cutoff {settle_time.isoformat()}.",
            )
        else:
            diff_days = (candidate.timestamp - settle_time).total_seconds() / 86400.0
            return (
                False,
                TemporalStatus.OUTSIDE_WINDOW,
                f"Candidate timestamp {candidate.timestamp.isoformat()} occurred {diff_days:.1f} days AFTER settlement cutoff {settle_time.isoformat()}.",
            )
