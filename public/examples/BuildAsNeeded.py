while CompareNumber(GetFromComponent("c_assembler",1),0):
	P1=1

P1 = GetFromComponent("Robotic", 2)
if CanProduce(P1):
    P2 = FactionItemAmount(P1)
    P3 = P1-P2
    if CompareNumber(P3,0):
        SetToComponent(P3, "c_assembler",1)