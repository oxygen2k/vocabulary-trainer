import json
import csv 
import random
import datetime 

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
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(vocabulary, file, ensure_ascii=False, indent=4)

#Sprache auswählen
def choose_language():
    print("Verfügbare Sprachen:")
    available = {
        "1": ("de-en", "english"),
        "2": ("de-fr", "french"),
        "3": ("de-es", "spanish")
    }
    for key, val in available.items():
        print(f"{key}: {val}")

    choice = input("Wähle eine Sprache!")
    return available.get(choice, None)

#Intervall-Berechnung
def calculate_next_due(level):
    today = datetime.date.today()
    intervals = [1, 2, 4, 7, 14, 30]
    interval_days = intervals[min(level, len(intervals) - 1)]
    return (today + datetime.timedelta(days=interval_days)).isoformat()

#Vokabeln hinzufügen (json)
def add_vocab(file_path, foreign_key):
    vocabulary = get_vocabulary(file_path)
    german = input("Deutsches Wort (oder 'x' zum Abbrechen): ")
    if german.lower() == "x":
        return
    
    if any(vocab["german"] == german for vocab in vocabulary):
        print(f"Die Vokabel '{german}' exisitiert bereits in deiner Liste.")
        return
    
    foreign_word = input(f"{foreign_key.capitalize()} Wort (oder 'x' zum Abbrechen): ")
    if foreign_word.lower() == "x":
        return

    new_vocab = {
        "german": german, 
        foreign_key: foreign_word,
        "level": 0,
        "mode": "learn",
        "next_due": datetime.date.today().isoformat()
    }

    vocabulary.append(new_vocab)
    save_vocabulary(file_path, vocabulary)
    print(f"Vokabel '{german}' - '{foreign_word}' wurde hinzugefügt.")

#Vokabeln hinzufügen via CSV
def import_from_csv(file_path, csv_path, foreign_key):
    vocabulary = get_vocabulary(file_path)

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            german, foreign_word = row
            if german in {vocab["german"] for vocab in vocabulary}:
                print(f"Die Vokabel '{german}' exisitiert bereits in deiner Liste.")
                continue

            new_vocab = {
                "german": german,
                foreign_key: foreign_word,
                "level": 0,
                "mode": "learn",
                "next_due": datetime.date.today().isoformat()
            }
            vocabulary.append(new_vocab)
    save_vocabulary(file_path, vocabulary)
    print(f"Vokabeln aus {csv_path} importiert.")

#Lernmodus
def study_mode(vocabulary, foreign_key):
    print("Lernmodus gestartet - Du entscheidest, ob Du es wusstest!")

    learn_vocab = [vocab for vocab in vocabulary if vocab.get("mode") == "learn"]

    if not learn_vocab:
        print("Keine Vokabeln im Lernmodus.")
        return

    random.shuffle(learn_vocab)

    for vocab in learn_vocab:
        answer = input(f"Was heißt: {vocab['german']}? (Enter für Lösung oder 'x' zum Beenden)")
        if answer == "x":
            print("Lernmodus beendet.")
            break
        
        print(f"Lösung: {vocab[foreign_key]}")
        feedback = input("Wusstest Du's? (j/n):")

        if feedback == "j":
            vocab["level"] += 1
            vocab["mode"] = "test"
            vocab["next_due"] = calculate_next_due(vocab["level"])
        
        else:
            vocab["level"] = 0
            vocab["next_due"] = calculate_next_due(0)

#Prüfungsmodus
def test_mode(vocabulary, foreign_key):
    today = datetime.date.today()

    due_vocab = [vocab for vocab in vocabulary if  vocab.get("mode") == "test" and datetime.date.fromisoformat(vocab["next_due"]) <= today]
    
    if not due_vocab:
        print("Keine Vokabeln sind heute fällig. Übe erst im Lernmodus.")
        return
    
    print("Prüfungsmodus gestartet - Tippe die Lösung ein!")
    random.shuffle(due_vocab)

    for vocab in due_vocab:
        answer = input(f"Was heißt: {vocab['german']} (Lösung eintippen oder 'x' zum Beenden)?")
        if answer.lower() == "x":
            print("Prüfungsmodus beendet.")
            break
        elif answer.lower() == vocab[foreign_key].lower():
            print("Richtig!")
            vocab["level"] += 1
            vocab["next_due"] = calculate_next_due(vocab["level"])
        else: 
            print(f"Falsch. Richtige Antwort: {vocab[foreign_key]}")
            if vocab["level"] > 0:
                vocab["level"] -= 1
                vocab["next_due"] = calculate_next_due(vocab["level"])
            else:
                vocab["mode"] = "learn"
                vocab["next_due"] = datetime.date.today().isoformat()

#Hauptprogramm
def main():
    while True:
        language_info = choose_language()
        if not language_info:
            print("Ungültige Auswahl.")
            return
    
        language, foreign_key = language_info
        file_path = f"{language}.json"
        vocabulary = get_vocabulary(file_path)

        while True:
            print("--- Vokabeltrainer ---")
            print("1 = Lernmodus")
            print("2 = Prüfungsmodus")
            print("3 = Neue Vokabel hinzufügen")
            print("4 = Vokabeln aus CSV importieren")
            print("9 = Zurück zur Sprachauswahl")
            print("0 = Beenden")
            chose_mode = input("Modus wählen: ")

            if chose_mode == "1":
                study_mode(vocabulary, foreign_key)
                save_vocabulary(file_path, vocabulary)
            elif chose_mode == "2":
                test_mode(vocabulary, foreign_key)
                save_vocabulary(file_path, vocabulary)
            elif chose_mode == "3":
                add_vocab(file_path, foreign_key)
                vocabulary = get_vocabulary(file_path)
            elif chose_mode == "4":
                csv_path = input("Pfad zur CSV-Datei (oder 'x' zum Abbrechen): ")
                if csv_path.lower() == "x":
                    continue 
                else:
                    import_from_csv(file_path, csv_path, foreign_key)
                    vocabulary = get_vocabulary(file_path)
            elif chose_mode == "9":
                break
            elif chose_mode == "0":
                print("Bis zum nächsten Mal!")
                return 
            else:
                print("Ungültige Eingabe!")

if __name__ == "__main__":
    main()  