from openai import OpenAI
client = OpenAI() 

response = client.responses.create(
    model="gpt-4o-mini",
    input="In one word, what's david's last name"
)

print(response.output_text)
