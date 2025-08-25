from openai import OpenAI
import os

# Initialize the client
client = OpenAI(api_key="b9df99ea41435fa7be5ce346b486c33e", base_url="https://gateway.chat.sensedeal.vip/v1/")


def main():
    response = client.chat.completions.create(
        model="qwen2.5-32b-instruct-int4", messages=[{"role": "user", "content": "Hello! How are you?"}]
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
