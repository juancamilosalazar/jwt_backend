import random 

decisioncomputadora = random.randint(1,3)


decisionmia = int(input("Decida piedra = 1, papel = 2, tijera = 3"))
print(decisioncomputadora)


if((decisioncomputadora == 1 and decisionmia ==1) or (decisioncomputadora == 2 and decisionmia ==2) or (decisioncomputadora == 3 and decisionmia ==3)  ):
    print("empate")
if((decisioncomputadora == 1 and decisionmia ==2) or (decisioncomputadora == 2 and decisionmia ==3) or (decisioncomputadora == 3 and decisionmia ==1)):
    print("ganaste")
if((decisioncomputadora == 1 and decisionmia ==3) or (decisioncomputadora == 2 and decisionmia ==1) or (decisioncomputadora == 3 and decisionmia ==2)):
    print("perdiste")