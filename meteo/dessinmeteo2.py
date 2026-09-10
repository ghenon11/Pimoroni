import unicornhat as uh
from time import sleep
from random import randint

uh.set_layout(uh.PHAT)
uh.brightness(0.5)

digits4 = {
    "-": ["000",
          "010",
          "010",
          "000"],

    0: ["111",
        "101",
        "101",
        "111"],

    1: ["010",
        "110",
        "010",
        "111"],

    2: ["111",
        "001",
        "111",
        "100"],

    3: ["111",
        "001",
        "111",
        "001"],

    4: ["101",
        "101",
        "111",
        "001"],

    5: ["111",
        "100",
        "111",
        "001"],

    6: ["111",
        "100",
        "111",
        "111"],

    7: ["111",
        "001",
        "001",
        "001"],

    8: ["111",
        "101",
        "111",
        "111"],

    9: ["111",
        "101",
        "111",
        "001"]
}

digits3 = {
    "-": [
        "000",
        "111",
        "000"
    ],

    0: [
        "111",
        "101",
        "111"
    ],

    1: [
        "010",
        "110",
        "010"
    ],

    2: [
        "111",
        "001",
        "110"
    ],

    3: [
        "111",
        "001",
        "111"
    ],

    4: [
        "101",
        "111",
        "001"
    ],

    5: [
        "111",
        "100",
        "111"
    ],

    6: [
        "111",
        "100",
        "111"
    ],

    7: [
        "111",
        "001",
        "001"
    ],

    8: [
        "111",
        "101",
        "111"
    ],

    9: [
        "111",
        "101",
        "111"
    ]
}



class Meteo_draw:

    def delete_all(self):
        uh.clear()
        uh.show()

    def show_temp(self, tmax=0,tmin=0):
            for y in [0,3]:
                for x in range(8):
                    col = (x*5)*6
                    uh.set_pixel(x=x,y=y,r=col,g=0,b=255-col)
            for x in range(int(tmax/5)+1):
                uh.set_pixel(x=x,y=1,r=(tmax*6),g=0,b=(255-(tmax*6)))
            for x in range(int(tmin/5)+1):
                uh.set_pixel(x=x,y=2,r=(tmin*6),g=0,b=(255-(tmin*6)))
                
    def show_units(self, units, r, g, b):
        leds = units            # nombre total de LEDs à afficher
        cols = [5, 6, 7]        # ordre de remplissage

        for col in cols:
            if leds <= 0:
                break

            # max 3 LEDs par colonne
            n = min(leds, 3)

            # remplir de bas en haut : y = 2,1,0
            for i in range(n):
                y = 2 - i
                uh.set_pixel(col, y, r, g, b)

            leds -= n

        
    def show_units(self, units, r, g, b):
        leds = units
        cols = [5, 6, 7]  # ordre de remplissage

        for col in cols:
            if leds <= 0:
                break

            # max 3 LEDs par colonne
            n = min(leds, 3)

            # remplir du bas vers le haut : y = 3,2,1
            for i in range(n):
                y = 3 - i
                uh.set_pixel(col, y, r, g, b)

            leds -= n

    def show_periods(self, period):
    
    #    Affiche 2 LEDs vertes pour la période donnée (0 à 3)
    #   sur la ligne y = 0.
      

        # mapping des colonnes par période
        mapping = {
            0: [0, 1],
            1: [2, 3],
            2: [4, 5],   # ✔ correction
            3: [6, 7]
        }

        cols = mapping.get(period, [])

        for col in cols:
            uh.set_pixel(col, 0, 0, 255, 0)   # vert

    


    def show_temp_columns(self, temp):

        t = max(-19, min(50, temp))
        is_negative = t < 0
        t_abs = abs(t)

        tens = t_abs // 10
        units = t_abs % 10

        # couleur thermique
        if t <= 0:
            r, g, b = 0, 0, 255
        elif t >= 39:
            r, g, b = 255, 0, 0
        else:
            t_norm = t / 39
            r = int(t_norm * 255)
            g = 0
            b = int((1 - t_norm) * 255)

        # --- DIZAINES : colonne 3 (max 3 LEDs, bottom-up y=3,2,1)
        for i in range(min(tens, 3)):
            y = 3 - i
            uh.set_pixel(3, y, r, g, b)

        # --- UNITÉS ---
        if units == 0:
            # digit "0"
            for y in range(3):
                for x in range(3):
                    if digits3[0][y][x] == "1":
                        uh.set_pixel(5 + x, y+1, r, g, b)
        else:
            self.show_units(units, r, g, b)

        # --- Signe négatif ---
        if is_negative:
            uh.set_pixel(0, 1, 0, 0, 255)
            uh.set_pixel(0, 2, 0, 0, 255)






    def show_probarain(self,prain):
        if prain <5:
            y=0
        elif prain>=5 and prain<25:
            y=1
        elif prain>=25 and prain<50:
            y=2
        elif prain>=50 and prain<75:
            y=3
        else:
            y=4
        for line in range(y):
            uh.set_pixel(x=0,y=line,r=0,g=255,b=255)
            uh.set_pixel(x=1,y=line,r=0,g=255,b=255)
            
    
    def show_weather(self,ob="sun"):
        if ob=="cl":
            self.delete_all()
            x=[7,6,5,4,3,4,5,6]
            y=[2,3,3,3,2,1,1,1]
            for nb in range(len(x)):
                uh.set_pixel(x=x[nb],y=y[nb],r=255,g=255,b=255)

        elif ob=="rain":
            x=[3,6,6,4,4]
            y=[0,1,0,2,1]
            for nb in range(len(x)):
                uh.set_pixel(x=x[nb],y=y[nb],r=randint(0,10),g=0,b=randint(240,255))

        elif ob =="sun":
            self.delete_all()
            x=[6,6,5,5,7,7,4,4]
            y=[1,2,1,2,0,3,3,0]
            for nb in range(len(x)):
                uh.set_pixel(x=x[nb],y=y[nb],r=170,g=170,b=0)
            
        elif ob=="snow":
            x=[7,4,5]
            y=[0,0,2]
            for nb in range(len(x)):
                uh.set_pixel(x=x[nb],y=y[nb],r=255,g=255,b=255)

        else:
            x=None
            y=None

def test():
    cl = Meteo_draw()
    while True:
        cl.show(ob="cl")
        uh.show()
        sleep(5)
        cl.show(ob="snow")
        uh.show()
        sleep(5)
        cl.show(ob="rain")
        uh.show()
        sleep(5)
        cl.show(ob="sun")
        uh.show()
        sleep(5)
        cl.delete_all()
        sleep(5)

if __name__ == "__main__":
    test()
        
