# 🏋️ Fitness Tracker — Back-end PPM 2026

**Tipo progetto:** Full-Stack Web Application
**Framework:** Django 4.2
**Traccia 5:** Fitness Tracking Application
**Studente:** Andrea Bertini

---

## 1. Descrizione

Applicazione web per il tracciamento degli allenamenti. L'atleta registra workout (forza/cardio),
serie e obiettivi e ne monitora i progressi; il coach segue i propri atleti assegnati e lascia
feedback sui singoli allenamenti.

## 2. Architettura

### MVT (Model-View-Template)
- **Model** (`accounts/models.py`, `workouts/models.py`): `CustomUser`, `WorkoutLog`,
  `ExerciseSession`, `ExerciseSet`, `Goal`. Modello relazionale con ForeignKey
  (es. un `WorkoutLog` ha N `ExerciseSession`, ognuna con N `ExerciseSet`) e self-FK
  `coach → athletes`.
- **View** (`workouts/views.py`): fungono da controller, applicano la logica CRUD e i
  controlli di accesso prima di rendere il template.
- **Template** (`templates/`): ereditarietà DRY da `base.html` tramite `{% extends %}` e `{% block %}`.

### RBAC (Role-Based Access Control)
Due ruoli sul `CustomUser` (`is_coach`):
- **Atleta (standard user):** gestisce i propri allenamenti, serie e obiettivi.
- **Coach:** accede alla dashboard dei propri atleti e scrive il `coach_feedback` sui loro log.

Il controllo è applicato su due livelli (*defense in depth*):
1. **Dominio (view):** le query filtrano sempre per proprietario
   (`request.user.athletes`, `WorkoutLog.objects.filter(user=athlete)`) → niente accesso
   orizzontale / IDOR.
2. **Presentazione (template):** menù e pulsanti differenziati con `{% if user.is_coach %}`.

## 3. Funzionalità per ruolo

**Atleta**
- CRUD allenamenti (crea/modifica/elimina), gestione esercizi e serie.
- Obiettivi con calcolo automatico della percentuale di completamento.

**Coach**
- Dashboard con elenco atleti assegnati.
- Dettaglio atleta con storico allenamenti e form rapido per il feedback.

## 4. Account demo (per i test)

| Ruolo  | Username       | Password      | Note                              |
|--------|----------------|---------------|-----------------------------------|
| Atleta | `atleta_demo`  | `atleta12345` | Ha allenamenti, serie e obiettivo |
| Coach  | `coach_demo`   | `coach12345`  | Segue `atleta_demo`               |
| Admin  | `admin`        | (superuser)   | Accesso a `/admin/`               |

> Il DB `db.sqlite3` è già pre-popolato con questi account e dati demo.

## 5. Installazione locale

```bash
# 1. Clona il repository
git clone <URL_REPO>
cd fitness_tracker_project

# 2. Crea e attiva l'ambiente virtuale
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Installa le dipendenze
pip install -r requirements.txt

# 4. Applica le migrazioni (il DB demo è già incluso; questo passo è idempotente)
python manage.py migrate

# 5. Avvia il server di sviluppo
python manage.py runserver
```

App disponibile su `http://127.0.0.1:8000/` → login con un account demo.

### Ricreare il DB da zero (opzionale)
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## 6. Deploy (Render / Railway)

`ALLOWED_HOSTS` accetta `localhost` e, in automatico, il dominio pubblico di Render
tramite la variabile `RENDER_EXTERNAL_HOSTNAME`. I file statici sono serviti da WhiteNoise.

```bash
# Build (eseguito dalla piattaforma)
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Start command
gunicorn django_project.wsgi
```

Account demo per la commissione:

| Ruolo  | Username      | Password      |
|--------|---------------|---------------|
| Atleta | `atleta_demo` | `atleta12345` |
| Coach  | `coach_demo`  | `coach12345`  |

## 🌐 Deploy Online
Il progetto è distribuito e raggiungibile pubblicamente al seguente indirizzo:
**URL Deploy:** [https://fitness-tracker-ppm.onrender.com](https://fitness-tracker-ppm.onrender.com)

## 7. Test rapido nel browser
1. Login come `coach_demo` → si apre la **Dashboard Coach** con `atleta_demo`.
2. Click su *Gestisci* → storico allenamenti dell'atleta.
3. Scrivi un feedback e salva → viene memorizzato sul `WorkoutLog`.
4. Logout, login come `atleta_demo` → crea un allenamento, aggiungi esercizi/serie e verifica gli obiettivi.
5. **Test permessi (azione vietata):** da `atleta_demo`, prova a visitare `/coach/atleta/<id>/`
   (area riservata al coach) → risposta **403 Forbidden**, nessun accesso ai dati di altri utenti.

