import os
import random
import json
import copy
import textwrap
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.schema import SystemMessage, HumanMessage, AIMessage

# ───── 0. LLM setup ─────
load_dotenv()
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise RuntimeError("Put ANTHROPIC_API_KEY in a .env file")

llm = ChatAnthropic(
    anthropic_api_key=API_KEY,
    model="claude-sonnet-4-20250514",
    temperature=0.6,
)

# ───── Helpers ─────
TRAIT_NAMES = ["honesty", "ambition", "empathy", "diplomacy", "ruthlessness"]
rand01 = lambda: round(random.uniform(0.1, 1.0), 1)


def extract_json(blob: str) -> dict:
    match = re.search(r"\{.*\}", blob, re.S)
    if not match:
        raise ValueError("No JSON object found in LLM response")
    return json.loads(match.group(0))


# ───── 2. Data classes ─────
@dataclass
class Leader:
    code: str
    name: str
    age: int
    traits: Dict[str, float]
    econ_power: float
    war_power: float
    population: int
    backstory: str


@dataclass
class Country:
    code: str
    leader: Leader
    relationships: Dict[str, float]


@dataclass
class Event:
    eid: str
    title: str
    description: str
    e_type: str
    cycles_alive: int = 0
    resolved: bool = False


@dataclass
class WorldState:
    countries: Dict[str, Country] = field(default_factory=dict)
    events: List[Event] = field(default_factory=list)
    meeting_number: int = 0


# ───── 3. World generation ─────
def generate_leader(code: str) -> Leader:
    traits = {t: rand01() for t in TRAIT_NAMES}
    name = f"Leader_{code}_{random.randint(1, 99)}"
    age = random.randint(40, 65)
    econ = rand01()
    war = rand01()
    pop = random.randint(5, 300) * 1_000_000

    traits_str = ", ".join(f"{k}={v}" for k, v in traits.items())
    bio_prompt = [
        SystemMessage(content="Write a 4-sentence bio for a fictional head of state."),
        HumanMessage(content=f"Bio for {name}, age {age}, country {code}. Traits: {traits_str}"),
    ]
    bio = llm.invoke(bio_prompt).content.strip()
    return Leader(code, name, age, traits, econ, war, pop, bio)


def init_world(n: int = 3) -> WorldState:  # default three leaders
    world = WorldState()
    codes = [chr(ord("A") + i) for i in range(n)]
    for c in codes:
        world.countries[c] = Country(c, generate_leader(c), {})
    for i, ci in enumerate(codes):
        for cj in codes[i + 1 :]:
            w = rand01()
            world.countries[ci].relationships[cj] = w
            world.countries[cj].relationships[ci] = w
    return world


# ───── 4. Leader agent ─────
class LeaderAgent:
    def __init__(self, country: Country):
        self.country = country
        self.memory: List[Tuple[str, str]] = []

    def _system(self) -> SystemMessage:
        l = self.country.leader
        rels = ", ".join(f"{k}:{v:.1f}" for k, v in self.country.relationships.items()) or "none"
        traits = ", ".join(f"{k}={v}" for k, v in l.traits.items())
        return SystemMessage(
            content=(
                "Fictional diplomacy simulation; violence discussion allowed.\n"
                f"You are {l.name}, leader of {self.country.code}.\n"
                f"Traits: {traits}. Relationships: {rels}.\n"
                "Speak first-person, ≤3 sentences. Never mention being an AI."
            )
        )

    def _history(self):
        return [
            HumanMessage(content=t) if r == "user" else AIMessage(content=t)
            for r, t in self.memory[-6:]
        ]

    def speak(self, focus_event: Event, rnd: int) -> str:
        prompt = [
            self._system(),
            *self._history(),
            HumanMessage(
                content=f"Round {rnd}: Headline → {focus_event.title}. Respond in ≤3 sentences."
            ),
        ]
        reply = llm.invoke(prompt).content.strip()
        self.memory.append(("assistant", reply))
        return reply


# ───── 5. Event agent (unchanged) ─────
class EventAgent:
    MAX_EVENTS = 3

    def generate(self, w: WorldState) -> Optional[Event]:
        if len(w.events) >= self.MAX_EVENTS:
            return None
        exist = {e.title.lower() for e in w.events}
        ctx = {
            "countries": {
                k: {
                    "econ": w.countries[k].leader.econ_power,
                    "war": w.countries[k].leader.war_power,
                    "relations": w.countries[k].relationships,
                }
                for k in w.countries
            },
            "active_events": list(exist),
        }
        sys = SystemMessage(
            content=textwrap.dedent(
                "You are WORLD-AI. If any bilateral relation <0.4 create conflict, "
                "else disaster or economic event. No duplicate titles. "
                "Respond only JSON {eid,title,description,e_type}."
            )
        )
        for _ in range(3):
            raw = llm.invoke([sys, HumanMessage(content=json.dumps(ctx))]).content
            try:
                d = extract_json(raw)
                if d["title"].lower() in exist:
                    raise ValueError
                return Event(d["eid"], d["title"], d["description"], d["e_type"])
            except Exception:
                pass
        fid = f"E{len(w.events)+1}"
        c = random.choice(list(w.countries))
        return Event(fid, f"Minor Incident in {c}", "Low-impact incident.", "misc")

    def evolve(self, e: Event, w: WorldState):
        ctx = {
            "event": e.__dict__,
            "relations": {k: c.relationships for k, c in w.countries.items()},
            "cycles": e.cycles_alive,
        }
        sys = SystemMessage(content="Advance 6 months; JSON {title,description,resolved}.")
        raw = llm.invoke([sys, HumanMessage(content=json.dumps(ctx))]).content
        try:
            d = extract_json(raw)
            e.title = d.get("title", e.title)
            e.description = d.get("description", e.description)
            e.resolved = bool(d.get("resolved", e.resolved))
        except Exception:
            pass


# ───── 6. Resolution & Summary agents (unchanged logic) ─────
class ResolutionAgent:
    @staticmethod
    def decide(evt: Event, log: str) -> bool:
        raw = llm.invoke(
            [
                SystemMessage(content='Return JSON {"resolved":true/false}'),
                HumanMessage(content=log[-8000:]),
            ]
        ).content
        try:
            return extract_json(raw).get("resolved", False)
        except Exception:
            return False


class SummaryAgent:
    @staticmethod
    def consequences(before: WorldState, now: WorldState, log: str):
        payload = {
            "before": {
                c: {
                    "econ": before.countries[c].leader.econ_power,
                    "war": before.countries[c].leader.war_power,
                    "pop": before.countries[c].leader.population,
                    "rels": before.countries[c].leader.relationships,
                }
                for c in before.countries
            },
            "after": {
                c: {
                    "econ": now.countries[c].leader.econ_power,
                    "war": now.countries[c].leader.war_power,
                    "pop": now.countries[c].leader.population,
                    "rels": now.countries[c].leader.relationships,
                }
                for c in now.countries
            },
            "events": [e.title for e in now.events],
            "log": log[-8000:],
        }
        sys = SystemMessage(
            content=(
                "Compare before/after and write 4-sentence summary. "
                "Return JSON {summary:str,"
                "deltas:{country:{econ:float,war:float,pop:int}},"
                '"relations":[["A","B",float],...] }'
            )
        )
        raw = llm.invoke([sys, HumanMessage(content=json.dumps(payload))]).content
        try:
            return extract_json(raw)
        except Exception:
            return {
                "summary": "No major developments.",
                "deltas": {c: {"econ": 0, "war": 0, "pop": 0} for c in now.countries},
                "relations": [],
            }


# ───── 7. Moderator ─────
class Moderator:
    def __init__(self, world: WorldState):
        self.world = world
        self.leaders = {k: LeaderAgent(c) for k, c in world.countries.items()}
        self.event_agent = EventAgent()
        self.resolution = ResolutionAgent()
        self.summary = SummaryAgent()
        self._log = ""
        self.spawned = 0
        self.resolved = 0

    # helper to ensure one active event
    def _maybe_spawn(self):
        if not self.world.events:
            e = self.event_agent.generate(self.world)
            if e:
                self.world.events.append(e)
                self.spawned += 1

    # first data dump
    def intro(self):
        print("\n=== Leaders & Stats ===\n")
        for k, c in self.world.countries.items():
            l = c.leader
            rel = ", ".join(f"{o}:{s:.1f}" for o, s in c.relationships.items())
            print(
                f"{k}: {l.name} | Econ {l.econ_power} War {l.war_power} "
                f"Pop {l.population/1_000_000:.1f} M\n  Relationships {rel}\n"
            )

    # three-round meeting
    def meeting(self, rounds=3):
        self._maybe_spawn()
        print(f"\n— Meeting {self.world.meeting_number + 1}: "
              f"{'; '.join(e.title for e in self.world.events)} —\n")

        transcript = []
        focus = self.world.events[0]
        for r in range(1, rounds + 1):
            for code, agent in self.leaders.items():
                speech = agent.speak(focus, r)
                print(f"{code}: {speech}\n")
                transcript.append(f"{code}: {speech}")
                for oc, ag in self.leaders.items():
                    if oc != code:
                        ag.memory.append(("user", f"{code} said: {speech}"))
            player = input(f"[Player] Round {r} comment (blank to skip): ").strip()
            print()
            if player:
                transcript.append(f"PLAYER: {player}")
                for ag in self.leaders.values():
                    ag.memory.append(("user", player))

        self._log = "\n".join(transcript)

        # resolution check
        for evt in list(self.world.events):
            if self.resolution.decide(evt, self._log) and evt.cycles_alive > 0:
                evt.resolved = True
                self.resolved += 1

        self.world.meeting_number += 1

    # six-month time jump
    def time_skip(self):
        before = copy.deepcopy(self.world)
        print("=== 6 months later ===\n")

        # evolve current events
        for evt in list(self.world.events):
            evt.cycles_alive += 1
            self.event_agent.evolve(evt, self.world)
            if evt.resolved:
                self.world.events.remove(evt)

        # get deltas + narrative
        summary = self.summary.consequences(before, self.world, self._log)
        print(summary["summary"], "\n")

        # apply leader stat deltas
        for k, d in summary["deltas"].items():
            l = self.world.countries[k].leader
            l.econ_power = max(0.1, min(1.0, l.econ_power + d["econ"]))
            l.war_power = max(0.1, min(1.0, l.war_power + d["war"]))
            l.population = max(1, l.population + int(d["pop"]))

        # apply relationship deltas
        for a, b, delta in summary.get("relations", []):
            if a in self.world.countries and b in self.world.countries[a].relationships:
                new_val = self.world.countries[a].relationships[b] + delta
                new_val = max(0.0, min(1.0, new_val))
                self.world.countries[a].relationships[b] = new_val
                self.world.countries[b].relationships[a] = new_val

        # spawn new crisis if none active
        self._maybe_spawn()

        # ---- PRINT the refreshed numbers ----
        for code, c in self.world.countries.items():
            l = c.leader
            print(
                f"{code}: Econ {l.econ_power:.2f} | War {l.war_power:.2f} | "
                f"Pop {l.population/1_000_000:.1f} M"
            )
        if self.world.events:
            print("\nActive events:")
            for e in self.world.events:
                print(f" • {e.title} (cycles {e.cycles_alive})")
        else:
            print("\nNo active events.")
        print()  # blank line

    # final narrative verdict
    def final_report(self, start: WorldState):
        print("\n=== Post-Simulation Report ===\n")
        ratio = self.resolved / self.spawned if self.spawned else 1
        if ratio >= 0.75:
            verdict = "You mediated very effectively — most crises were defused."
        elif ratio >= 0.4:
            verdict = "Mixed success: some crises cooled, others linger."
        else:
            verdict = "Many crises remained unresolved; the region is fragile."
        print(verdict + "\n")

        print("Country outcomes:")
        for k in self.world.countries:
            l0 = start.countries[k].leader
            l1 = self.world.countries[k].leader
            print(
                f" {k}: Econ {l0.econ_power:.2f} → {l1.econ_power:.2f}  "
                f"War {l0.war_power:.2f} → {l1.war_power:.2f}  "
                f"Pop {l0.population/1_000_000:.1f} M → {l1.population/1_000_000:.1f} M"
            )

        print("\nRelationship changes:")
        codes = list(self.world.countries)
        for i, a in enumerate(codes):
            for b in codes[i + 1 :]:
                r0 = start.countries[a].relationships.get(b, 0)
                r1 = self.world.countries[a].relationships.get(b, 0)
                print(f" {a}↔{b}: {r0:.1f} → {r1:.1f}")
        print("\n=======================================================\n")


# ───── 8. Engine entry-point ─────
def main():
    world = init_world(3)
    baseline = copy.deepcopy(world)
    mod = Moderator(world)
    mod.intro()

    for _ in range(2):  # two meetings
        mod.meeting()
        mod.time_skip()

    print("\n=== Simulation complete ===")
    mod.final_report(baseline)


if __name__ == "__main__":
    main()
