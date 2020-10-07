import json

with open("info.txt", encoding="utf8") as file:
    info = json.load(file)

info["last_message"] = """Λόγω περιορισμών που έχει πλέον η δωρεάν έκδοση του Google Meet θα στραφούμε στο Zoom.To URL για Λειτουργικά Συστήματα Ι και Μεταγλωττιστές είναι: https://zoom.us/j/92364042060Passcode: 395173Για Λειτουργικά Συστήματα ΙΙ:https://zoom.us/j/92698569623"""
with open("info.txt", "w", encoding="utf8") as file:
    json.dump(info, file, indent=4)

print(info)