def MarkTowers(lonelytower, placement):
  '''
  Places a cross-hair of foundations around potential spots for new towers.
  Towers boot up "lonely" and needing acknowledgement - they will broadcast Small Relay
  Until they're acknowledged.

  Example is intended to stress test loops and to encourage me to implement for range.
  '''
  lonelytower = _
  gridsize = 10
  for potential, _ in LoopSignalMatch("v_letter_A"):
    lonelytower = potential
  Signal = lonelytower
  location_x, location_y = SeparateCoordinate(GetLocation(lonelytower))

  marker_x = location_x - 10
  while marker_x <= location_x + 10:
    marker_y = location_y - 10
    while marker_y <= location_y + 10:
        delta_x = -1
        while delta_x <= 1:
            delta_y = -1
            while delta_y<=1:
                placement = CombineCoordinate(marker_x+delta_x, marker_y+delta_y)
                PlaceConstruction(placement ,0, bp={"frame":"f_foundation"} ) 

                delta_y+=2
            delta_x+=2
        marker_y+=10
    marker_x+=10