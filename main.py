import os
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()

console = Console()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def ask_model(prompt: str):
    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key not found. Check your .env file.")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "google/gemma-3-4b-it:free",
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(url, headers=headers, json=data)

    result = response.json()
    return result["choices"][0]["message"]["content"]


if __name__ == "__main__":
    clear_terminal()
    prompt = str(input("Ask anything: "))
    limit_question = str(input("Limit response by maximum words? (y/n) "))

    if limit_question not in ["y", "n"]:
        print('Invalid response. Use "y" or "n" only.')

    reply = ""

    if limit_question == "y":
        limit = input("Enter word limit (in numbers): ")
        if limit.isdigit():
            reply = ask_model(f"{prompt}\n\nLimit your response to {limit} words.")
            console.print("\nResponse:")
            console.print(Markdown(reply))
        else:
            print("Invalid response. Use numbers only.")
    elif limit_question == "n":
        reply = ask_model(prompt)
