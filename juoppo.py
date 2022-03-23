import logging
import sqlite3

from dataclasses import dataclass, field
from datetime import datetime


"""VAKIOMÄÄRITTELYT

   Määritellään vakioita merkitsemään erilaisia muuttumattomaksi oletettuja
   asioita. Vakioille on hyvä antaa nimiä, ettei koodiin jää kovin paljon
   ns. taikanumeroita, eli selittämättömiä lukuarvoja, joiden merkitys täytyy
   vain tietää. Nimeäminen antaa niille semantiikkaa ja helpottaa koodin
   ymmärtämistä.

   Oikeastaan nämä ovat muuttujia, mutta koska Python, ne kirjoitetaan
   käpseillä. Sitten on vain sovittu, että näin kirjoitettuihin juttuihin ei
   satuta. Jotkin ohjelmointikielet asettavat oikeita rajoja, mutta Python on
   hyvin liberaali sen suhteen, että kuka saa sattua ja mihin. Kaikki perustuu
   yhteisymmärrykseen, vähän kuin oikeassakin maailmassa. Osin kai siksi Python
   onkin niin joustava. Asiassa on hyvät ja huonot puolensa.

   Pythonissa myös ihan kaikki on olioita. Funktiokin on olio. Siinäkin on
   omat hyvät ja huonot puolensa.
"""

"""Suomen Valtion Virallisen Etyylialkoholiannoksen määritykset.

Alkoholiannos on epämääräinen suure, joka vastaa määritelmällisesti
10 - 12 grammaa alkoholia. Toki, kuka minä olen tuomitsemaan. Juonhan minäkin
määritelmällisesti yhden oluen, oli se sitten millainen vain. Tällainen
kannustaa "yhden juomiseen", kun ei olla tarkkoja asioista eikä varmasti ole
lainkaan hyvää alkoholipolitiikkaa! """
PORTION_SMALL_G = 10 
PORTION_LARGE_G = 12


ETHANOL_WEIGHT = 790 # Etanolilitran paino grammoissa
DEFAULT_ROUND_TO = 2


"""
Eri merkkijonoja
"""

# Virheilmoituksia
ERR_WTF=("What the FATAL?!1. Nyt pistit kyllä pahan ja tapoit koko ohjelman. "
         "Tämä on hyvin odottamatonta. Alla on paljon insinööritietoa, joka voi "
         "auttaa selvittämään tämänkin haasteen! Ohjelman kehittäjä olisi hyvin "
         "huolissaan, jos kuulisi tapahtuneesta.")

# Tiedostonimiä
FILENAME_DB = "juoppodata.db"
FILENAME_LOG = "juoppo.log"



"""AlcoholicBeverage
   
   Koko tämän hetkinen toteutus pyörii tämän luokan olioiden ympärillä. 'Luokan
   olioiden' on tässä vain hieno tapa sanoa, että tässä on nyt dataa ja siihen
   liittyviä toimintoja saatavilla monenlaisten abstraktioiden ympäröimänä.

   Toistaiseksi en tarvinnut muuta kuin rakenteen, johon tuikata yhteenkuuluvia
   datapisteitä. Datapainotteisuutta painottamaan ja elämää helpottamaan
   merkitsin luokan vielä tuollaisella @decorator-koristeella varsinaiseksi
   dataluokaksi.

   Näin toimimalla minun ei tarvitse esim. kirjoittaa erikseen
   rakentajametodia. Lisäksi saan koodata tavanomaista
   luokkasyntaksia coolimmalla tavalla. Joudun toki vähän puuttumaan
   oletusalustajan toimintaan __post_init__():ssä. Sellaista vain joutuu kai
   joskus tekemään. Tässä kohtaa avasin jo ensimmäisen kerran StackOverflow:n.
   En löytänyt ulkomuistista, että millaisella himmelillä sainkaan lisättyä
   mukaan myös laskettuja arvoja rakennusvaiheessa. Toki arvot olisi voinut
   laskea valmiiksi myös ennen olion luomista, esim. erillisessä funktiossa
   mutta kun nyt tällaisia himmeleitä on tarjolla, niin käytetään niitä hyväksi.
   Jonathan Blowta mukaillen: Uskon, että tämä on hyvä tapa menestyä
   ohjelmistoalalla.

   Osa datasta valuu tupiin käyttäjältä komentorivin kautta, osa lasketaan itse.
   Se tuntui luonnolliselta, sillä käyttäjän syötettä lukevaa laskukonettahan
   tässä yritetäänkin komentaa.

   Mystinen `field(init=False)` hoitaa sellaisen jutun, että saan alustaa kyseiset
   muuttujat ainakin osittain itse taianomaisen valmisalustajan sijaan
   __post_init__():ssä. Haluan laskea niihin  muutaman käyttäjän syötteeseen
   perustuvan arvon. Näin saan vain tarvitsemiani kokonais- ja liukulukuja
   näppärästi samaan nippuun.

   Ylikirjoitan myös metodin __repr__(), että saan luokan elukoista print():llä
   konsoliin mieleiseni tulosteen.
"""

@dataclass
class AlcoholicBeverage:
    producer: str
    name: str
    volume: float
    abv_percent: float
    abv_fraction: float = field(init=False)
    alc_l: float = field(init=False)
    alc_g: float = field(init=False)
    portions_small: float = field(init=False)
    portions_large: float = field(init=False)


    def __post_init__(self):
        self.abv_fraction = self.abv_percent / 100
        self.alc_l = round(self.abv_fraction * self.volume, DEFAULT_ROUND_TO)
        self.alc_g = round(self.alc_l * ETHANOL_WEIGHT, DEFAULT_ROUND_TO)
        self.portions_small = round(self.alc_g / PORTION_SMALL_G, DEFAULT_ROUND_TO)
        self.portions_large = round(self.alc_g / PORTION_LARGE_G, DEFAULT_ROUND_TO)

    def __repr__(self):
        return (
            f"{self.producer} - {self.name}\n"
            f"Määrä: {self.volume} l\n"
            f"Alkoholivahvuus (ABV): {self.abv_percent} %\n"
            f"Alkoholi litroina: {self.alc_l} l\n"
            f"Alkoholi grammoina: {self.alc_g} g\n"
            f"Valtion Virallisia Alkoholiannoksia: {self.portions_large} - {self.portions_small}\n")


"""Pääfunktio main()

Sitä voisi luulla, että homma alkaa tästä, koska tämä on main()-funktio, mutta ei.
Varsinainen aloituskohta on vielä pääsilmukan alapuolella. Mutta pääsilmukka
kun on, tähän päädytään ihan siitä sitten seuraavana. Tässä funktiossa
vietetäänkin sitten loppuohjelma.

Funktio alkaa parilla alustuksella, joissa määritellään nimiä viittamaan eri
asioihin ja siirrytään sitten ikikieriöön. Tämä on hyvin tyypillinen tapa tehdä
tietokoneohjelma. Useimmat niistä mylläävät aina jossain luupissa, vaikkeivat
sitä välttämättä helpolla myönnäkään.

Vastaavia toimenpiteitä suoritetaan pääsilmukan alun jälkeen asioille, jotka ovat
järjellisiä yhden silmukankierähdyksen ajan. Itse koodaillessani pyrin pitämään
muuttujat ja muut viittaukset aina mahdollisimman pienillä näkyvyysalueilla,
koska se tuppaa selkiyttämään ohjelmaa ja on yleisesti myös hyväksytty ihan
asialliseksi tavaksi menestyä ohjelmistoalalla.

Muutama vähän peruskurssista eroava pythonismi:
0) with ... as ... -rakenne, eli ns. context manager, jolla voi helposti käyttää esim.
   tiedostoja ilman, että tarvitsee murehtia niiden eksplisiittisestä
   sulkemisesta. Esim. tässä pitäisi olla db_con.close() lopussa, mutta
   context manager hoitaa sen maagisesti.
1) try-except-else, jossa else-lohko ajetaan, mikäli ei tullut mitään poikkeusta.
2) =: mursuoperaattori, jolla sijoituslausekkeen saa käyttäytymään C:mäisemmin,
   eli palauttamaan sijoituslausekkeen lopputuloksen. Mahdollistaa
   vähän tiiviimmän esitystavan. Tätä tuskin koskaan varsinaisesti tarvitsee,
   mutta on oikein kivan näköinen juttu tehdä joskus.
3) List comprehension, [derp.do() for derp in derps], pythonimainen tapa toimia
   listojen kanssa. Käy moneen, esim. for-silmukoiden korvikkeeksi.
4) Pythonin versio C:n ternarysta, jolla voi kirjoittaa hämmentäviä yhden rivin
   ehtolausekkeita.

Muutenhan tämä on melkein kuin minkä tahansa perusohjelmointikurssin harkkatyö.

"""
def main():

    # Tunnistetaan eli autentikoidaan käyttäjä tarvittavan tietoturvallisesti
    # Luodaan hänet tietokantaan mikäli hän ei siellä jo ole ja jos on,
    # ladataan olemassa oleva tieto sieltä muistiin.
    #
    # SQL-lausekkeita ei sitten muuten ikinä saa tällä tavoin muodostaa raa'an
    # käyttäjäsyötteen pohjalta. Vihamielinen käyttäjä voisi laittaa vaikka
    # mitä maailmantuhoajaluokan tavaraa syötteeksi ja se menisi suoraan
    # tietokantakyselyyn mukaan. Näin softan valmistaja päätyisi
    # tietomurtolööppeihin. Ollaan luotu ns. SQL-injektiohaavoittuvuus. Onneksi
    # ei ole vielä vihamielisiä käyttäjiä! Tämä on kyllä syytä tehdä
    # ammattimaisemmin, mutten nyt vielä selvitä miten se tarkalleen hoidetaan
    # Pythonin sqlite3-kirjastolla, koska tämä koodi voidaan vielä heittää
    # kokonaan kuikkaan.
    user_input = input("Kuka juopottelee? ")

    with sqlite3.connect(FILENAME_DB) as db_con:
        db_cur = db_con.cursor()
        db_q = f"SELECT * FROM consumer WHERE nick_name LIKE '{user_input}'"
        db_cur.execute(db_q)
        user_data = db_cur.fetchone()

        if not user_data:
            logging.info("User data not found for user %s. Creating new user.", user_input)
            db_q = f"INSERT INTO consumer(nick_name, creation_timestamp) values ('{user_input}', '{datetime.now()}');"
            db_cur.execute(db_q)
            db_con.commit()
        else:
            # Koska SQLite3-rajapinta palauttaa tietokannan tietueet tupleina,
            # voidaan tehdä tällainen jännä sijoitusoperaatio useampaan
            # muuttujaan
            user_id, user_name, user_creation_timestamp = user_data
            logging.info("Found user %s with id %d created on %s", user_name, user_id, user_creation_timestamp)


    moar = True # moar main loop iterations!
    drinks = list()

    while (moar):
        producer = str(input("Alkoholijuoman valmistaja: "))
        name = str(input("Alkoholijuoman nimi: "))
        
        while True:
            vol_input = input("Juoman kokonaismäärä (l): ")
            try:
                vol = float(vol_input.replace(',', '.'))
            except ValueError:
                print(f"\"{vol_input}\" ei kyllä ole järkevä tilavuus litroina. Yritähän uudestaan.")
                continue
            else:
                break

        while True:
            abv_input = input("ABV (%): ")
            try:
                abv = float(abv_input.replace(',', '.'))
            except ValueError:
                print(f"\"{abv_input}\" ei kyllä ole järkevä alkoholitilavuus prosentteina. Yritähän uudestaan.")
                continue
            else:
                break

        drinks.append(AlcoholicBeverage(producer, name, vol, abv))

        while (input_moar := input("Vieläkö joit? (k/e)").lower()) not in ['k', 'e']:
            continue

        moar = True if input_moar == "k" else False


    print()
    [print(d) for d in drinks]
    
    print(f"YHTEENSÄ\n\n"
          f"Juotuja juomia (pullo/tölkki/tuoppi): {len(drinks)} kpl\n"
          f"Juoman kokonaismäärä: {sum(d.volume for d in drinks)} l\n"
          f"Alkoholia litroina: {sum(d.alc_l for d in drinks)} l\n"
          f"Alkoholia grammoina: {sum(d.alc_g for d in drinks)} g\n"
          f"Valtion Virallisia Annoksia: {sum(d.portions_large for d in drinks)} - {sum(d.portions_small for d in drinks)} kpl")


"""
Täältä ohjelman suoritus alkaa oikeasti. Vai alkaako? No kyllä näin voisi
sanoa. Tarkkoja jos ollaan, niin tuolla aivan ylimpänä ajetaan
import-komennot, joilla käytännössä tuodaan vain lisää leluja mukaan leikkiin,
eli otetaan käyttöön erilaisia Python-moduuleja. Python-tulkin tulkitsemaa
koodia sekin, mutta täältä se varsinainen ohjelma sitten alkaa.

Tällainen if __name__ on hyvin yleinen, suositeltava rakenne, mitä
Python-koodissa näkee. Tätä kannattaa käyttää. Tämä estää pääluuppia ajautumasta,
jos vaikka haluaisikin käyttää tätä koodia moduulina toisessa koodissa. Tämän voisi tällä haavaa jättää
poiskin. Tää tuntuu kuitenkin kuuluvan hyviin tapoihin, joten uhrataan yksi konditionaali hyvien tapojen
alttarille.

Sen jälkeen tehdään vähän alkuvalmisteluja. Otetaan käyttöön print()-käskyjä
edistyneempi logitus ja säädetään se minttiin. Lisäksi luodaan SQL-lausekkeilla
sopivat tietokantataulut, mikäli ne puuttuvat. Välittömästi tässä jo tulee
mieleen ORM-ratkaisujen hienous. Jos haluan joskus muuttaa tietokantaskeemaa,
pitää esim. tehdä itse jonkinlaiset migraatioskriptit ja tietokantarakenteen
versiointi tai sitten tunkata käsin. Hrr... Esim. joku SQLAlchemy voisi olla
tämän projektin puitteissa jännää ottaa haltuun.
"""
if __name__ == "__main__":

    logging.basicConfig(
        filename=FILENAME_LOG,
        encoding="utf-8",
        level=logging.DEBUG)


    with sqlite3.connect(FILENAME_DB) as con:

        # SQL-skriptin voisi siirtää varsinaisen ohjelmakoodin ulkopuoliseen
        # tiedostoon
        q = (f"CREATE TABLE IF NOT EXISTS consumer ("
             f"id INTEGER PRIMARY KEY, "
             f"nick_name TEXT, "
             f"creation_timestamp TIMESTAMP);"

             f"CREATE TABLE IF NOT EXISTS beverage ("
             f"id INTEGER PRIMARY KEY, "
             f"producer TEXT NOT NULL, "
             f"name TEXT NOT NULL, "
             f"size REAL NOT NULL);"

             f"CREATE TABLE IF NOT EXISTS consumption ("
             f"id INTEGER PRIMARY KEY, "
             f"timestamp TIMESTAMP, "
             f"beverage_id INTEGER, "
             f"consumer_id INTEGER, "
             f"FOREIGN KEY(beverage_id) REFERENCES beverage(id), "
             f"FOREIGN KEY(consumer_id) REFERENCES consumer(id));")

        con.executescript(q)
        con.commit()


    try:
        main()
    except Exception as e:
        print(ERR_WTF)
        raise
