
from core.orchestrator_ref import OrchestratorRef
orch = OrchestratorRef(['eval-with-caching','eval-jit-sim','eval-baseline'])
for i in range(50):
    r = orch.run_once(None,None, threshold=35.0)
    print(i, r['agent'], f"{r['time_ms']:.2f}ms")
