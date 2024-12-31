from inaSpeechSegmenter_bot.models import (
    OverallItem,
)

from inaSpeechSegmenter_api_models import (
    GetSegmentsResponse,
)

from typing import Dict, List

SEGMENT_EXCLUDE_LABELS = [
    "noEnergy",
    "noise",
]

def get_gendered_segments_overall(
    response: GetSegmentsResponse,
) -> List[OverallItem]:
    segments = response.segments

    per_label_durations: Dict[str, float] = {}

    total_duration = 0.0

    for segment in segments:
        if segment.label in SEGMENT_EXCLUDE_LABELS:
            continue

        segment_duration = segment.end_time - segment.start_time
        total_duration += segment_duration

        if segment.label not in per_label_durations:
            per_label_durations[segment.label] = 0.0

        per_label_durations[segment.label] += segment_duration

    return [
        OverallItem(
            label=label,
            ratio=duration / total_duration,
        )
        for label, duration in per_label_durations.items()
    ]
