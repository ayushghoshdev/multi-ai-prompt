import os
import requests
import base64
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from models import gpt_models, gemma_models, llama_models
from utils import clear_terminal

load_dotenv()

console = Console()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


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


def select_attachment():
    add_file = input("\nAdd attachment? (y/n): ")

    if add_file not in ["y", "n"]:
        console.print(Markdown("Invalid response. Use **y** or **n** only."))
        exit()

    file_content = None

    if add_file == "y":
        TEXT_EXTENSIONS = [".txt", ".py", ".md", ".json"]
        IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]

        file_path = input("Enter file path: ").strip().strip('"').strip("'")

        if not os.path.exists(file_path):
            print("File not found.")
            exit()

        ext = "." + file_path.split(".")[-1].lower()

        if ext in TEXT_EXTENSIONS:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
        elif ext in IMAGE_EXTENSIONS:
            with open(file_path, "rb") as f:
                base64_content = base64.b64encode(f.read()).decode("utf-8")
            mime = {
                "jpg": "jpeg",
                "jpeg": "jpeg",
                "png": "png",
                "gif": "gif",
                "webp": "webp",
            }[ext[1:]]
            file_content = ("image", base64_content, mime)
        else:
            print(
                "Unsupported file type. Supported text: txt, py, md, json; images: jpg, jpeg, png, gif, webp"
            )
            exit()

    return file_content


def choose_model():
    console.print("\nChoose a model family:")
    console.print("1 - GPT OSS")
    console.print("2 - Google Gemma")
    console.print("3 - Meta Llama")

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


def choose_model_attachment():
    console.print("\nChoose a model family:")
    console.print(
        "1 - [strike dim]GPT OSS[/strike dim] [dim]Unavailable for prompts with attachments[/dim]"
    )
    console.print("2 - Google Gemma")
    console.print("3 - Meta Llama")

    choice = input("Enter choice (2/3): ")

    if choice == "2":
        return gemma_models[0]
    elif choice == "3":
        return llama_models[0]
    else:
        console.print(Markdown("Invalid choice. Use **2** or **3** only."))
        exit()


def ask_model(model: str, prompt: str, file_content=None):
    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key not found. Check your .env file.")

    response = None

    try:
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        if file_content:
            if isinstance(file_content, str):
                content = f"{prompt}\n\nAttached file content:\n{file_content}"
            else:  # tuple ('image', base64, mime)
                content = [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{file_content[2]};base64,{file_content[1]}"
                        },
                    },
                ]
        else:
            content = prompt

        data = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
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
    file_content = select_attachment()
    if file_content:
        model = choose_model_attachment()
    else:
        model = choose_model()
    reply = ask_model(model, prompt, file_content)
    if reply:
        print()
        console.print(Markdown(f"{reply}"))
