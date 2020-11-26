MORSE_CHARS = {
    "A": ".-", "B": "-...",
    "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....",
    "I": "..", "J": ".---", "K": "-.-",
    "L": ".-..", "M": "--", "N": "-.",
    "O": "---", "P": ".--.", "Q": "--.-",
    "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--",
    "X": "-..-", "Y": "-.--", "Z": "--..",
    "1": ".----", "2": "..---", "3": "...--",
    "4": "....-", "5": ".....", "6": "-....",
    "7": "--...", "8": "---..", "9": "----.",
    "0": "-----", ", ": "--..--", ".": ".-.-.-",
    "?": "..--..", "/": "-..-.", "-": "-....-",
    "(": "-.--.", ")": "-.--.-"
}

DMORSE_CHARS = {v: k for k, v in MORSE_CHARS.items()}


def encrypt(message: str) -> str:
    cipher = ""
    for letter in message.upper():
        if letter != " ":
            try:
                cipher += f"{MORSE_CHARS[letter]} "
            except KeyError:
                pass
        else:
            cipher += "  /  "

    return cipher


def decrypt(message: str) -> str:
    if "/" in message:
        text = message.split("/")
    else:
        text = message.split("  ")

    cleaned_text = [item.strip() for item in text]

    output = []
    for word in cleaned_text:
        morse = " "
        for letter in word.split():
            try:
                morse += f"{DMORSE_CHARS[letter]} "
            except KeyError:
                pass
        output.append(morse)

    return " / ".join(output)
