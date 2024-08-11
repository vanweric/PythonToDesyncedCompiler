def UnpoweredConstructionHelper(target, potential):
  target = _
  for tower, potential in LoopSignalMatch("v_construction"):
    if not Match(potential, "v_in_powergrid"):
      target = SelectNearest(potential, target)

  target = SetNumber(target, 1)
  MoveUnit(target)