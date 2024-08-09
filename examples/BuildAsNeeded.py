def BuildAsNeeded(construction, tower, ingredient, needed):
  # This loop busy waits while the assembler is in use.
  # When compiled it won't have an explicit loop flow  
  # Since it is the first instruction, restarting the 
  # program is equivalent to restarting the loop.
    while GetFromComponent("c_assembler",1)>0:
  	    pass

    for tower, construction in LoopSignalMatch( "v_construction"):
        for ingredient in LoopRecipeIngredients(entity):
            if not CanProduce(ingredient):
                needed = ingredient - FactionItemAmount(ingredient)
                if needed > 0:
                    SetToComponent(needed, "c_assembler", 1)