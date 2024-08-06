import re
import json

import requests
from bs4 import BeautifulSoup as bs

from exceptions import(
        EasystaffLoginForm,
        EasystaffLogin,
        EasystaffBookingPage,
        EasystaffBooking,
)

FORM_URL = "https://orari-be.divsi.unimi.it/EasyAcademy/auth/auth_app.php??response_type=token&client_id=client&redirect_uri=https://easystaff.divsi.unimi.it/PortaleStudenti/index.php?view=login&scope=openid+profile"
LOGIN_URL = "https://cas.unimi.it/login"
EASYSTAFF_LOGIN_URL = "https://easystaff.divsi.unimi.it/PortaleStudenti/login.php?from=&from_include="

#per questi 3 non serve login
#da sistemare mese e anno per BIBLIO_URL_PRIMO e BIBLIO_URL_TERRA
BIBLIO_URL_PRIMO  = "https://prenotabiblio.sba.unimi.it/portalePlanningAPI/api/entry/50/schedule/2024-07/25/3600"
BIBLIO_URL_TERRA = "https://prenotabiblio.sba.unimi.it/portalePlanningAPI/api/entry/92/schedule/2024-07/25/3600"
BIBLIO_URL_PRIMO_PERS = "https://prenotabiblio.sba.unimi.it/portalePlanningAPI/api/entry/92/schedule/2024-07-16/50/{}?user_primary={}"
BIBLIO_URL_TERRA_PERS = "https://prenotabiblio.sba.unimi.it/portalePlanningAPI/api/entry/92/schedule/2024-07-16/25/{}?user_primary={}" #primo = durata, secondo = cf. posso ottenere cf da login

BIBLIO_BOOK = "https://prenotabiblio.sba.unimi.it/portalePlanningAPI/api/entry/store"
BIBLIO_CONFERMA = "https://prenotabiblio.sba.unimi.it/portalePlanningAPI/api/entry/confirm/{}"
INPUT_PRENOTAZOINE = {"cliente": "biblio", "start_time": {}, "end_time": {}, "durata": {}, "entry_type": 92, "area": 25, "public_primary": "CFRIMOSSO", "utente": {"codice_fiscale": "CFRIMOSSO", "cognome_nome": "RIMOSSO", "email": "RIMOSSO"}, "servizio": {}, "risorsa": None, "recaptchaToken": None, "timezone": "Europe/Rome"}

class Easystaff:
    def __init__(self):
        self._token = None
        self._session = requests.Session()


    def _get_login_form(self):
        res = self._session.get(FORM_URL)
        if not res.ok:
            raise EasystaffLoginForm(f"Couldn't fetch CAS form, responded with {res.status_code}")

        form_data = {
                "selTipoUtente": "S",
                "hCancelLoginLink": "http://www.unimi.it",
                "hForgotPasswordLink": "https://auth.unimi.it/password/",
                "service": "https://orari-be.divsi.unimi.it/EasyAcademy/auth/auth_app.php??response_type=token&client_id=client&redirect_uri=https://easystaff.divsi.unimi.it/PortaleStudenti/index.php?view=login&scope=openid+profile",
                "_eventId": "submit",
                "_responsive": "responsive",
        }

        form_soup = bs(res.text, "lxml")
        lt = form_soup.find_all(id="hLT")[0]["value"]
        execution = form_soup.find_all(id="hExecution")[0]["value"]

        form_data["lt"] = lt
        form_data["execution"] = execution
        return form_data


    def login(self, username: str, password: str):
        payload = self._get_login_form()
        payload["username"] = username
        payload["password"] = password

        res = self._session.post(LOGIN_URL, data=payload)
        if not res.ok:
            raise EasystaffLogin(f"Failed to login, responded with {res.status_code}")
        
        token_url = res.text[48:348]
        token_url = token_url[token_url.find("access_token") + 13:]
        res = self._session.post(
                EASYSTAFF_LOGIN_URL,
                data={"access_token": token_url}
        )
        if not res.ok:
            raise EasystaffLogin(f"Failed on access token, responded with {res.status_code}")


    def get_biblio(self, ciclo: int):
        if ciclo == 1:
            res = self._session.get(BIBLIO_URL_TERRA)
        else:
            res = self._session.get(BIBLIO_URL_PRIMO) 

        if not res.ok:
            raise EasystaffBookingPage(f"Failed to fetch bibio page, responded with {res.status_code}")

        biblio = json.loads(res.text)

        return biblio
    

    def get_freespot(self, ciclo: int):
        durata = 3600
        cf = "BNILRT03M26D918X"
        if ciclo == 1:
            res = self._session.get(BIBLIO_URL_TERRA_PERS.format(durata, cf))
        else :
            res = self._session.get(BIBLIO_URL_PRIMO_PERS.format(durata, cf))

        if not res.ok:
            raise EasystaffBookingPage(f"Failed to fetch freespot page, responded with {res.status_code}")
        
        biblio = json.loads(res.text)

        return biblio


    def book_bibio(self, TS_INIZIO: int, TS_FINE: int):
        INPUT_PRENOTAZOINE["start_time"]=TS_INIZIO
        INPUT_PRENOTAZOINE["end_time"]=TS_FINE
        INPUT_PRENOTAZOINE["duarata"]=TS_FINE-TS_INIZIO
        res = self._session.post(BIBLIO_BOOK, json=INPUT_PRENOTAZOINE)
        response_json = res.json()
        id = response_json["entry"]
        res = self._session.post(BIBLIO_CONFERMA.format(id))
        print(res.text)
        if not res.ok:
            raise EasystaffBooking(f"Failed to book biblio, responded with {res.status_code}")