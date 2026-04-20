import os
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()

console = Console()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

gpt_models = ["openai/gpt-oss-120b:free", "openai/gpt-oss-20b:free"]

gemma_models = [
    "google/gemma-3-4b-it:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-27b-it:free",
]

llama_models = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def get_limited_prompt(prompt: str):
    limit_question = input("\nLimit response by maximum words? (y/n): ")

    if limit_question not in ["y", "n"]:
        console.print(Markdown("Invalid response. Use **y** or **n** only."))
        exit()

    if limit_question == "y":
        limit = input("Enter word limit (in numbers): ")
        if not limit.isdigit():
            print("Invalid response. Use numbers only.")
            exit()

        return f"{prompt}\n\nLimit your response to {limit} words."

    return prompt


def choose_model():
    print("\nChoose a model family:")
    print("1. GPT OSS")
    print("2. Google Gemma")
    print("3. Meta Llama")

    choice = input("Enter choice (1/2/3): ")

    if choice == "1":
        return gpt_models[0]
    elif choice == "2":
        return gemma_models[0]
    elif choice == "3":
        return llama_models[0]
    else:
        console.print(Markdown("Invalid choice. Use **1** or **2** or **3** only."))
        exit()


def ask_model(model: str, prompt: str):
    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key not found. Check your .env file.")

    response = None

    try:
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }

        response = requests.post(url, headers=headers, json=data)

        result = response.json()

        if "error" in result:
            error = result["error"]
            code = error.get("code")
            message = error.get("message")

            print(f"\nOpenRouter API Error [{code}]: {message}")

            if "metadata" in error:
                print("Details:", error["metadata"].get("raw"))

            return None

        return result["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as http_err:
        if response is not None:
            error_info = response.json().get("error", {})
            code = error_info.get("code")
            message = error_info.get("message")

            print(f"HTTP error occurred: {http_err}")
            print(f"OpenRouter Error: [{code}] {message}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to OpenRouter.")
    except requests.exceptions.Timeout:
        print("Error: The request timed out.")
    except requests.exceptions.RequestException as err:
        print(f"An unexpected error occurred: {err}")


if __name__ == "__main__":
    clear_terminal()
    prompt = str(input("Ask anything: "))
    prompt = get_limited_prompt(prompt)
    model = choose_model()
    reply = ask_model(model, prompt)
    if reply:
        console.print(Markdown(f"\n{reply}"))
