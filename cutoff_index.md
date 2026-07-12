# cutoff: cut-off loops engine test (pulse 0.25s; 1=kick 2=snare 3=hat 4=cowbell 5=clave)

| # | structure | bar | starts |
|---|---|---|---|
| cut1 | (123 123 12) x2  — the original | 4.0s | 0:00.0 |
| cut2 | (1234 1234 123) x2 | 5.5s | 0:16.0 |
| cut3 | (12 12 12 1) x2 | 3.5s | 0:38.0 |
| cut4 | (12345 1234) x2 | 4.5s | 0:52.0 |
| cut5 | (12 12 1) x2 over a steady hat clock | 2.5s | 1:10.0 |
| cut6 | lanes cut differently: (12 12 1)x2 vs (45 45 4)x2 | 2.5s | 1:20.0 |
| cut7 | depth-2: (A A A-cut) where A=(123 123 12) | 5.75s | 1:30.0 |
