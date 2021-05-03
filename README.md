# siemens-spica-rilec

Vmesnik za prenos podatkov iz sistema Siemens SiPass v sistem Spica time&space.

Uporablja se na UL FRI za evidenco prisotnosti na delovnem mestu. Skupaj s tem programom na istih podatkih dela [spletna aplikacija registrator.fri.uni-lj.si](https://github.com/polz113/registrator).

## Kako deluje

### Nastavitve

Nastavitve so v datotekah *siemens\_spica\_settings.py* - poti z datotekami, *spica_api_settings.py* - ključ in URL Spica vmesnika.

#### siemens\_spica\_settings.py

- LOG\_GLOB - datoteke, ki jih ustvari Siemens SIPASS
- SPOOL\_DIR - imenik z dogodki; v tem imeniku je za vsako kadrovsko št. podimenik.

- SPOOL\_FNAME - ime datoteke z dogodki, ki še niso bili obdelani
- OLDEVENTS\_FNAME - ime datoteke z dogodki, ki so bili obdelani / poslani naprej
- FIX\_FNAME - datoteka s popravki tipov dogodkov

- NOCOMMIT\_FNAME - datoteka, v katero se zapisujejo vklopi/izklopi prenašanja v SAP za zaposlenega

#### spica\_api\_settings.py

- *APIURL* - URL, ki ga dobimo od Špice
- *SPICA\_USER* - uporabnik, ki ga dobimo od Špice
- *SPICA\_PASSWD* - geslo za uporabnika, ki ga dobimo od Špice
- *SPICA\_KEY* - API ključ, ki ga dobimo od Špice

### Uporaba

- Sistem siemens v imenik pošlje datoteke room-access\*.csv, ki vsebujejo kadrovsko številko in točen čas (siemensfiles).
- `siemens\_to\_spool.py` dogodke v datotekah, ki ustrezajo LOG\_GLOB, razporedi po kadrovskih številkah znotraj SPOOL\_DIR, jih prekodira v UTF-8 in predela datume v standardni format; odstrani podvojene dogodke.
- `add_fix.py` ustvari popravek v FIX\_FNAME. Vsak popravek vsebuje čas popravka in tip, v katerega se spremeni zadnji dogodek pred tem časom. Takšne popravke lahko ustvarja tudi spletna aplikacija.
- `fix_events.py`.
- `spool_to_spica` prenese podatke v sistem Špica Time and Space, ki jih potem prenese naprej v APIS. Pri tem za vsakega uporabnika preveri, ali v imeniku z dogodki obstaja NOCOMMIT\_FNAME (nocommit.csv); če ne obstaja ali se ne konča z "1", potem podatke pošlje naprej.


## Kako se dejansko uporablja

Glej datoteko push\_siemens\_to\_spica.sh

## Spletna aplikacija

Za nastavljanje tipov dogodkov se lahko namesto `add\_fix.py` uporablja spletna aplikacija registrator.
