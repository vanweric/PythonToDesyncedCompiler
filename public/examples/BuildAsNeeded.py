def BuildAsNeeded(construction, tower, ingredient, needed):
  '''
  Looks for construction sites (via the Radar Tower) that are missing items
  Checks how many are needed vs how many are already present 
  Builds if needed.
  '''

  # This loop busy waits while the assembler is in use.
  while GetFromComponent("c_assembler",1)>0:
    pass

  for tower, construction in LoopSignalMatch( "v_construction"):
    for ingredient in LoopRecipeIngredients(construction):
      # Note: CanProduce has it's flow outputs flipped from 90% of instructions :-(
      if not CanProduce(ingredient):
        needed = ingredient - FactionItemAmount(ingredient)
        if needed > 0:
          SetToComponent(needed, "c_assembler", 1)