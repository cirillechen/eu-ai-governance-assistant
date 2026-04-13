import json
import requests

API_URL = "http://127.0.0.1:8000/ask"

def evaluate():
    with open("evaluation_questions.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    total = len(test_cases)
    success = 0

    for i, case in enumerate(test_cases, 1):
        question = case["question"]
        expected_keywords = case["expected_keywords"]

        print(f"\n--- Test {i} ---")
        print(f"Q: {question}")

        try:
            response = requests.post(
                API_URL,
                json={"question": question},
                timeout=60
            )

            answer = response.json()["answer"].lower()

            match = all(keyword.lower() in answer for keyword in expected_keywords)

            if match:
                print("✅ PASS")
                success += 1
            else:
                print("❌ FAIL")
                print("Answer:", answer[:200])

        except Exception as e:
            print("⚠️ ERROR:", e)

    print("\n====================")
    print(f"Score: {success}/{total}")
    print("====================")

if __name__ == "__main__":
    evaluate()