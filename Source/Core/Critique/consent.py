"""Natural-language informed-consent parser for a previously critiqued plan."""

import re

from Source.Core.Critique.plan_critic import PlanCritic, UserDecision


class ConsentParser:
    APPROVE = ("yine de uygula", "yinede uygula", "devam et", "kabul ediyorum", "onayliyorum", "apply anyway", "proceed anyway")
    REJECT = ("uygulama", "iptal", "vazgec", "vazgeç", "dur", "cancel", "do not apply")

    def apply_reply(self, plan, reply):
        normalized = re.sub(r"\s+", " ", (reply or "").casefold()).strip()
        if any(phrase in normalized for phrase in self.REJECT):
            return PlanCritic.apply_decision(plan, UserDecision(False, reply))
        if any(phrase in normalized for phrase in self.APPROVE):
            return PlanCritic.apply_decision(plan, UserDecision(True, reply))
        raise ValueError("Reply does not contain an informed approval or rejection.")
