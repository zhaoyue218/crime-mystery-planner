from __future__ import annotations

from llm_interface import LLMBackend
from models import CaseBible, PlotPlan


class StoryRealizer:
    def __init__(self, llm: LLMBackend) -> None:
        self.llm = llm

    def realize(self, case_bible: CaseBible, plot_plan: PlotPlan) -> str:
        opening = (
            f"{case_bible.title}\n\n"
            f"{case_bible.setting} was supposed to host an elegant retreat, "
            f"but by the time Detective Lena Marlowe arrived, the estate had hardened into a trap. "
            f"{case_bible.victim.name} lay dead, the road was swallowed by snow, and every face in the hall carried some private fear.\n"
        )

        body_parts: list[str] = []
        for step in plot_plan.steps:
            participants = ", ".join(step.participants)
            evidence = ", ".join(step.evidence_ids) if step.evidence_ids else "no physical exhibit yet"
            paragraph = (
                f"\n[{step.step_id}] {step.title}\n"
                f"At {step.timeline_ref or 'an uncertain hour'}, in the {step.location.lower()}, {step.summary} "
                f"The active participants were {participants}. "
                f"The step centered on {evidence}. "
                f"What emerged was this: {'; '.join(step.reveals) if step.reveals else 'the pressure inside the estate increased.'}"
            )
            body_parts.append(paragraph)

        closing = (
            "\n\nBy the final reconstruction, the case no longer depended on rumor. "
            f"The deleted footage, the message to the map room, the digitalis trace, and the staged outage formed a single chain that pointed to {case_bible.culprit.name}. "
            f"He had used his control over security to create opportunity, his grudge to supply motive, and a poisoned spike to provide method. "
            f"{self.llm.generate('Generate story closing line').text}"
        )
        return opening + "".join(body_parts) + closing
