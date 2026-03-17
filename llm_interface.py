from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass
class LLMResponse:
    text: str


class LLMBackend:
    def generate(self, prompt: str) -> LLMResponse:
        raise NotImplementedError


class MockLLMBackend(LLMBackend):
    def __init__(self, seed: int = 7) -> None:
        self._rng = Random(seed)

    def generate(self, prompt: str) -> LLMResponse:
        prompt_key = prompt.lower()
        if "title" in prompt_key:
            choices = [
                "The Last Lantern at Blackstone Hall",
                "Murder Beneath the Clocktower Snow",
                "The Winter Gala Cipher",
            ]
        elif "setting" in prompt_key:
            choices = [
                "Blackstone Hall, a snowbound estate converted into a private criminology retreat",
                "Harbor House Museum during a fundraiser held through a night storm",
                "Ashdown Conservatory during a closed-door academic symposium",
            ]
        elif "story" in prompt_key:
            choices = [
                "The truth surfaced only when the smallest contradiction stopped looking small.",
                "Every polished alibi cracked once the evidence was forced into sequence.",
                "The case turned when motive, timing, and physical trace finally aligned.",
            ]
        else:
            choices = [
                "A hidden grudge shaped the crime more than any public argument.",
                "The strongest clue looked ordinary until it was placed against the timeline.",
                "The culprit relied on confusion, not invisibility.",
            ]
        return LLMResponse(text=self._rng.choice(choices))
