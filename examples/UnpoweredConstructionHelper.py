def UnpoweredConstructionHelper(target, potential):
  '''
  Finds construction sites outside the logistics network and stands next to them.
  This adds them to the logisitics network long enough to have deliveries scheduled
  '''
  # Standard Search Loop to find a target
  target = _
  for tower, potential in LoopSignalMatch("v_construction"):
    if not Match(potential, "v_in_powergrid"):
      target = SelectNearest(potential, target)
  # The number sets the distance from the target.
  # We want to stand next to it, not on top of it blocking construction
  target = SetNumber(target, 1)
  MoveUnit(target)