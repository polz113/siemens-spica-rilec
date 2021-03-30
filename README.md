# siemens-spica-rilec

Vmesnik za prenos podatkov iz sistema Siemens SiPass v sistem Spica time&space.

Uporablja se na UL FRI za evidenco prisotnosti na delovnem mestu.

## Kako deluje

Sistem siemens v imenik pošlje datoteke room-access\*.csv, ki vsebujejo kadrovsko številko in točen čas (siemensfiles).
Spletna aplikacija registrator pošlje datoteke event-types\*.csv, ki vsebujejo kadrovsko številko, čas, tip dogodka (typefiles).

Aplikacija prebere typefiles. Zapomni si vse vnose za današnji dan.

Aplikacija prebere dogodke iz sistema Siemens. Doda jim tipe po algoritmu:
  - za vsak vnos v typefiles poišče dogodek iz siemensfiles, ki se je zgodil pred tem znotraj istega dne in mu nastavi tip
  - za vsak vnos, ki nima tipa dogodka, izbere privzeti tip (prihod).

Spletna aplikacija vsak večer ob 21h ustvari datoteko v typefiles, kjer vsem zaposlenim spremeni zadnji dogodek v odhod.


