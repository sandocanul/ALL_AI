import google.generativeai as genai

# Pune cheia ta reală aici (aia care începe cu AIzaSy...)
genai.configure(api_key="AIzaSyBMJy1AO70RFcMYi8onNyfL6KJCkgJUmtM")

print("Modele disponibile pentru generare de text:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)