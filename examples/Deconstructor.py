def Deconstructor(target):
  target = _
  for potential in LoopSignalMatch("v_arrow_down"):
    target = SelectNearest(potential, target)
  SetToComponent(target,"c_deconstructor")
  while Match(target, "v_building"):
    pass