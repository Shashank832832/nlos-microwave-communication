# Legacy collaborator reference

`collaborator_v1/` contains the original root-level FDTD solver and its solver-dependent comparison/visualization scripts. They are retained for historical comparison, not for active runs. Their field convention is y-first (`Ez[ny, nx]`) and their API is incompatible with the active Member 2 solver. The production package imports only `src.fdtd.solver` and the Member 3 source in `src/sources/`.

The original Member 2/Member 3 incoming files remain unchanged under `reference_material/incoming/`.
