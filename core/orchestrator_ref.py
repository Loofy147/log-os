
"""Reference Python adapter to simulate the L0 orchestrator behavior.
This allows running experiments until the Log-Os interpreter loads L0 files.
"""
import random, time, statistics
from collections import defaultdict

# Simple probes implemented in Python to mimic L0 evaluators
def eval_baseline(ast, env):
    t0 = time.time()
    # simulate work
    work = random.uniform(0.02, 0.06)
    time.sleep(work*0)  # no sleep to keep fast
    t1 = t0 + work
    return {"value": None, "time_ms": (t1-t0)*1000, "strategy":"baseline"}

def eval_with_caching(ast, env, cache):
    # emulate cache hit/miss probabilistically
    t0 = time.time()
    hit = random.random() < 0.7
    work = 0.01 if hit else 0.04
    t1 = t0 + work
    return {"value": None, "time_ms": (t1-t0)*1000, "strategy":"cache_hit" if hit else "cache_miss"}

def eval_jit_sim(ast, env, state):
    t0 = time.time()
    # simulate initial high compile cost sometimes
    compile_cost = 0.05 if random.random() < 0.3 else 0.0
    exec_cost = 0.02
    t1 = t0 + compile_cost + exec_cost
    return {"value": None, "time_ms": (t1-t0)*1000, "strategy":"jit"}

class OrchestratorRef:
    def __init__(self, agents):
        # agents: list of strings like 'eval-with-caching', 'eval-jit-sim', 'eval-baseline'
        self.state = {a: {"alpha":1.0, "beta":1.0, "trials":0, "wins":0} for a in agents}

    def random_beta(self, alpha, beta):
        # use two gamma draws via random.gammavariate
        x = random.gammavariate(alpha,1.0)
        y = random.gammavariate(beta,1.0)
        return x/(x+y)

    def sample_agent(self):
        draws = {a: self.random_beta(s["alpha"], s["beta"]) for a,s in self.state.items()}
        return max(draws.items(), key=lambda kv: kv[1])[0]

    def update(self, agent, time_ms, threshold):
        s = self.state[agent]
        success = 1 if time_ms <= threshold else 0
        s["trials"] += 1
        s["wins"] += success
        s["alpha"] += success
        s["beta"] += (1 - success)

    def run_once(self, ast, env, threshold):
        agent = self.sample_agent()
        if agent == "eval-with-caching":
            res = eval_with_caching(ast, env, {})
        elif agent == "eval-jit-sim":
            res = eval_jit_sim(ast, env, {})
        else:
            res = eval_baseline(ast, env)
        self.update(agent, res["time_ms"], threshold)
        return {"agent": agent, "time_ms": res["time_ms"], "res": res}

if __name__ == '__main__':
    orch = OrchestratorRef(['eval-with-caching','eval-jit-sim','eval-baseline'])
    # run some simulated runs
    records = []
    for _ in range(200):
        r = orch.run_once(None, None, threshold=35.0)
        records.append(r)
    import json
    with open('orchestrator_ref_results.json','w') as f:
        json.dump(records, f, indent=2)
    print('Wrote orchestrator_ref_results.json')
