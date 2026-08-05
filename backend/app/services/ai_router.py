from groq import Groq
from app.config import get_settings

settings = get_settings()


def generate_ai_response(
    prompt: str, 
    model_name: str = "groq", 
    system_instruction: str = "Ești un asistent AI util, inteligent și prietenos."
) -> str:
    """
    Rutează cererea către furnizorul de AI selectat.
    """
    model_key = model_name.lower()

    if model_key == "groq":
        if not settings.groq_api_key:
            return "⚠️ Eroare: Cheia API pentru Groq nu este setată în fișierul .env!"

        # Inițializăm SDK-ul oficial Groq
        client = Groq(api_key=settings.groq_api_key)

        # Apelăm modelul Llama-3.3-70b (ultra-rapid)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
        )

        return completion.choices[0].message.content

    elif model_key == "gemini":
        return "[PlaceHolder] Modelul Gemini va fi legat în pasul următor."

    elif model_key == "claude":
        return "[PlaceHolder] Modelul Claude va fi legat în pasul următor."

    else:
        return f"⚠️ Modelul '{model_name}' nu este suportat încă."