from collections import Counter
class Metrics:
    def __init__(self): self.counters=Counter()
    def inc(self,name,n=1): self.counters[name]+=n
    def snapshot(self): return dict(self.counters)
metrics=Metrics()
