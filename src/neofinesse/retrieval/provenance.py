import time
from typing import List

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.retrieval.base import (
    BaseRetrievalStrategy,
    EvidenceCandidate,
    RetrievalResult,
    RetrievalStrategy,
    TemporalRetrievalStatus,
)
from neofinesse.retrieval.relationship import RelationshipAwareRetrievalStrategy


class TypedProvenanceRetrievalStrategy(BaseRetrievalStrategy):
    """Strategy 4: Typed Provenance Retrieval verifying full cell/file provenance chains."""

    strategy_name = RetrievalStrategy.TYPED_PROVENANCE

    def __init__(self):
        self._rel_strategy = RelationshipAwareRetrievalStrategy()

    def retrieve(
        self, case_id: str, settlement_id: str, target_variance: int, dataset: IngestedDataset
    ) -> RetrievalResult:
        start_time = time.perf_counter()

        # Retrieve base relationship candidates
        base_result = self._rel_strategy.retrieve(case_id, settlement_id, target_variance, dataset)

        enhanced_candidates: List[EvidenceCandidate] = []
        fully_provenanced_count = 0
        incomplete_provenance_count = 0

        for cand in base_result.candidates:
            prov = cand.provenance
            is_valid = False
            audit_metadata = {}

            if prov:
                has_file = bool(prov.source_file and prov.source_file.strip())
                has_row = bool(prov.source_row and prov.source_row >= 1)
                has_source_hash = bool(prov.source_hash and len(prov.source_hash) == 64)
                has_record_hash = bool(prov.record_hash and len(prov.record_hash) == 64)
                has_provider = bool(prov.provider)

                is_valid = has_file and has_row and has_source_hash and has_record_hash and has_provider

                audit_metadata = {
                    "source_id": prov.source_id,
                    "source_type": prov.source_type.value if prov.source_type else "UNKNOWN",
                    "source_file": prov.source_file,
                    "source_sheet": prov.source_sheet,
                    "source_row": prov.source_row,
                    "source_columns": prov.source_columns,
                    "source_hash": prov.source_hash,
                    "record_hash": prov.record_hash,
                    "provider": prov.provider.value if prov.provider else None,
                    "ingested_at": prov.ingested_at.isoformat() if prov.ingested_at else None,
                    "provenance_status": "VERIFIED" if is_valid else "PROVENANCE_INCOMPLETE",
                }

            if is_valid:
                fully_provenanced_count += 1
            else:
                incomplete_provenance_count += 1
                audit_metadata["provenance_status"] = "PROVENANCE_INCOMPLETE"

            cand_copy = cand.model_copy(
                update={
                    "is_provenance_complete": is_valid,
                    "evidence_metadata": {**cand.evidence_metadata, **audit_metadata},
                }
            )
            enhanced_candidates.append(cand_copy)

        latency = (time.perf_counter() - start_time) * 1000.0
        return RetrievalResult(
            case_id=case_id,
            settlement_id=settlement_id,
            strategy=self.strategy_name,
            target_variance=target_variance,
            candidates=enhanced_candidates,
            rejected_candidates=base_result.rejected_candidates,
            retrieval_latency_ms=latency,
            retrieval_metadata={
                "fully_provenanced_count": fully_provenanced_count,
                "incomplete_provenance_count": incomplete_provenance_count,
                "provenance_coverage_pct": (fully_provenanced_count / max(1, len(enhanced_candidates))) * 100.0,
            },
        )
