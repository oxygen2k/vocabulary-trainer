import json
import csv 
import random
import datetime 
import streamlit as st
import os, tempfile, json

#HILFSFUNKTIONEN

#JSON einlesen
def get_vocabulary(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            vocabulary = json.load(file)
            for vocab in vocabulary:
                if "mode" not in vocab:
                    vocab["mode"] = "learn"
                    vocab["level"] = 0
                    vocab["next_due"] = datetime.date.today().isoformat()
            return vocabulary 
    except FileNotFoundError:
        return []
    
#JSON speichern
def save_vocabulary(file_path, vocabulary):
    """Atomisch in JSON speichern (temp file + replace)."""
    dirpath = os.path.dirname(file_path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dirpath, prefix="vocab_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(vocabulary, f, ensure_ascii=False, indent=4)
        # os.replace muss im try-Block sein, damit bei einem Fehler
        # die temporäre Datei im finally-Block sicher gelöscht wird.
        os.replace(tmp_path, file_path)
    except Exception as e:
        # Optional: Fehler loggen, um die Ursache zu sehen
        st.error(f"Fehler beim Speichern der Datei: {e}")
    finally:
        # falls tmp noch existiert (z.B. bei Fehler in os.replace), löschen
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

#Intervall-Berechnung
def calculate_next_due(level):
    today = datetime.date.today()
    intervals = [1, 2, 4, 7, 14, 30]
    interval_days = intervals[min(level, len(intervals) - 1)]
    return (today + datetime.timedelta(days=interval_days)).isoformat()

#----------
#UI START
#----------
st.set_page_config(page_title="Vokabeltrainer", layout="centered")
st.title("Vokabeltrainer")

#Sprache auswählen
language_display = {
    "Deutsch-Englisch": ("de-en", "english"),
    "Deutsch-Französisch": ("de-fr", "french"),
    "Deutsch-Spanisch": ("de-es", "spanish")
}
choose_language = st.sidebar.selectbox("Sprache wählen", list(language_display.keys()))
language, foreign_key = language_display[choose_language] 
file_path = f"{language}.json"

#Modus wählen
mode = st.sidebar.radio("Modus wählen", ["Lernmodus", "Prüfungsmodus", "Vokabelübersicht", "Neue Vokabel hinzufügen", "Vokabeln aus CSV importieren"])
vocabulary = get_vocabulary(file_path)

#Vokabeln hinzufügen (json)
if mode == "Neue Vokabel hinzufügen":
    vocabulary = get_vocabulary(file_path)
    german = st.text_input("Deutsches Wort:")
    foreign_word = st.text_input(f"{foreign_key.capitalize()} Wort:")
    if st.button("Hinzufügen"):
        if any(vocab["german"].lower() == german.lower() for vocab in vocabulary):
            st.warning(f"'{german}' existiert bereits.")
        else:
            vocabulary.append({
                "german": german, 
                foreign_key: foreign_word,
                "level": 0,
                "mode": "learn",
            "next_due": datetime.date.today().isoformat()
            })
        save_vocabulary(file_path, vocabulary)
        st.success(f"Vokabel '{german}' - '{foreign_word}' wurde hinzugefügt.")

#Vokabeln hinzufügen via CSV
elif mode == "Vokabeln aus CSV importieren":
    vocabulary = get_vocabulary(file_path)
    uploaded = st.file_uploader("CSV-Datei hochladen", type="csv")
    if uploaded:
        reader = csv.reader(uploaded.read().decode("utf-8").splitlines(), delimiter=";")
        added = 0 
        for row in reader:
            german, foreign_word = row
            if any(vocab["german"].lower() == german.lower() for vocab in vocabulary): 
                continue
            vocabulary.append({
                "german": german,
                foreign_key: foreign_word,
                "level": 0,
                "mode": "learn",
                "next_due": datetime.date.today().isoformat()
            })
            added += 1
        save_vocabulary(file_path, vocabulary)
        st.success(f"Vokabeln wurden erfolgreich importiert.")

#Vokabeln anzeigen
elif mode == "Vokabelübersicht":
    st.header("Alle Vokablen")
    st.write(f"Anzahl aller Vokabeln: {len(vocabulary)}")
    if not vocabulary:
        st.info("Keine Vokabeln vorhanden.")
    else:
        header_cols = st.columns([3, 3, 2, 2, 2, 1])
        header_cols[0].write("Deutsch")
        header_cols[1].write(f"{foreign_key.capitalize()}")
        header_cols[2].write("Modus")
        header_cols[3].write("Fällig am")
        header_cols[4].write("Level")

        for i, vocab in enumerate(vocabulary):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 3, 2, 2, 2, 1])
            col1.write(vocab["german"])
            col2.write(vocab.get(foreign_key, ""))
            col3.write(vocab.get("mode", "-"))
            col4.write(vocab.get("next_due", "-"))
            col5.write(vocab.get("level", "-"))
            if col6.button("Löschen", key=f"del_{i}"):
                vocabulary.pop(i)
                save_vocabulary(file_path, vocabulary)
                st.experimental_rerun()

#Lernmodus
elif mode == "Lernmodus":
    if "lm_file" not in st.session_state or st.session_state.lm_file != file_path:
        if "due_today_list" in st.session_state:
            del st.session_state.due_today_list
        st.session_state.lm_file = file_path

    learn_vocab = [vocab for vocab in vocabulary if vocab.get("mode") == "learn"]
    today = datetime.date.today()
    due_today = [vocab for vocab in learn_vocab if datetime.date.fromisoformat(vocab["next_due"]) <= today]
    st.write(f"Anzahl Vokabeln im Lernmodus: {len(learn_vocab)}")
    st.write(f"Davon heute fällig: {len(due_today)}")

    if not due_today:
        st.info("Keine Vokabeln im Lernmodus.")
    else:
        if "due_today_list" not in st.session_state:
            st.session_state.due_today_list = random.sample(due_today, len(due_today))
            st.session_state.current_index = 0 
            st.session_state.show_solution = False
            st.session_state.feedback = None

        if st.session_state.current_index < len(st.session_state.due_today_list):
            vocab = st.session_state.due_today_list[st.session_state.current_index]
            st.write(f"**Was heißt:** {vocab['german']}")
    
            if not st.session_state.show_solution:
                if st.button("Lösung anzeigen"):
                    st.session_state.show_solution = True
                    st.experimental_rerun()
            else:
                st.write(f"Antwort: {vocab[foreign_key]}")
                st.session_state.feedback = st.radio("Wusstes Du's?", ["Ja", "Nein"], horizontal=True, key=f"fb_{vocab['german']}")

                if st.button("Weiter"):
                    # Vokabel im session_state aktualisieren
                    if st.session_state.feedback == "Ja":
                        vocab["level"] += 1
                        vocab["mode"] = "test"
                        vocab["next_due"] = datetime.date.today().isoformat()
                    else:
                        vocab["level"] = 0
                        vocab["next_due"] = calculate_next_due(vocab["level"])
                    
                    # Die aktualisierte Vokabel in der Hauptliste 'vocabulary' finden und ersetzen
                    # Das ist nötig, da 'vocabulary' bei jedem Rerun neu geladen wird.
                    for i, v in enumerate(vocabulary):
                        if v["german"] == vocab["german"]:
                            vocabulary[i] = vocab
                            break
                    
                    save_vocabulary(file_path, vocabulary)

                    st.session_state.current_index += 1
                    st.session_state.show_solution = False
                    st.session_state.feedback = None
                    st.experimental_rerun()

#Prüfungsmodus
elif mode == "Prüfungsmodus":
    today = datetime.date.today()
    test_vocab = [vocab for vocab in vocabulary if vocab.get("mode") == "test"]
    due_vocab = [vocab for vocab in test_vocab if datetime.date.fromisoformat(vocab["next_due"]) <= today]

    st.write(f"Anzahl Vokabeln im Prüfungsmodus: {len(test_vocab)}")
    st.write(f"Davon heute fällig: {len(due_vocab)}")

    if not due_vocab:
        st.info("Keine Vokabeln sind heute fällig. Übe erst im Lernmodus.")
    else:
        # Session State initialisieren oder zurücksetzen, wenn die Sprache wechselt
        if "pm_file" not in st.session_state or st.session_state.pm_file != file_path:
            st.session_state.pm_file = file_path
            st.session_state.due_vocab = random.sample(due_vocab, len(due_vocab))
            st.session_state.current_index = 0
            st.session_state.show_result = False
            st.session_state.last_check_correct = None
            st.session_state.last_check_answer = ""

        vocab_list = st.session_state.due_vocab

        if st.session_state.current_index >= len(vocab_list):
            st.success("Alle fälligen Vokabeln geprüft!")
            if st.button("Nochmal prüfen"):
                del st.session_state.pm_file # Löst eine Neuinitialisierung aus
                st.experimental_rerun()
        else:
            idx = st.session_state.current_index
            vocab = vocab_list[idx]

            st.write(f"Was heißt: **{vocab['german']}**?")

            if not st.session_state.show_result:
                with st.form(key=f"pm_form_{idx}"):
                    answer_input = st.text_input("Antwort eingeben:", key=f"ans_input_{idx}")
                    submitted = st.form_submit_button("Überprüfen")

                if submitted:
                    user_answer = (answer_input or "").strip().lower()
                    correct_answer = vocab[foreign_key].lower()
                    is_correct = (user_answer == correct_answer)

                    if is_correct:
                        vocab["level"] += 1
                    else:
                        vocab["level"] = max(0, vocab["level"] - 1)
                        vocab["mode"] = "learn" # Zurück in den Lernmodus bei Fehler

                    vocab["next_due"] = calculate_next_due(vocab["level"])
                    # Die aktualisierte Vokabel in der Hauptliste 'vocabulary' finden und ersetzen
                    for i, v in enumerate(vocabulary):
                        if v["german"] == vocab["german"]:
                            vocabulary[i] = vocab
                            break
                    
                    save_vocabulary(file_path, vocabulary)

                    st.session_state.show_result = True
                    st.session_state.last_check_correct = is_correct
                    st.session_state.last_check_answer = vocab[foreign_key]
                    st.experimental_rerun()
            else:
                # Ergebnis anzeigen
                if st.session_state.last_check_correct:
                    st.success("Richtig!")
                else:
                    st.error(f"Falsch. Richtige Antwort: {st.session_state.last_check_answer}")

                if st.button("Weiter", key=f"next_{idx}"):
                    st.session_state.current_index += 1
                    st.session_state.show_result = False
                    st.session_state.last_check_correct = None
                    st.session_state.last_check_answer = ""
                    st.experimental_rerun()