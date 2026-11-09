
import json
import time
from pathlib import Path

from project_a.data.natural_language_cases import NATURAL_LANGUAGE_CASES
from project_a.implementations.llm_based import ask_gemini

OUTPUT_PATH = Path("project_a/data/llm_results.json")


def load_previous_results():
    if OUTPUT_PATH.exists():
        with OUTPUT_PATH.open("r", encoding="utf-8") as file:
            return {
                item["case_id"]: item
                for item in json.load(file)
                if item["status"] == "success"
            }
    return {}


def save_results(results):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            sorted(results.values(), key=lambda x: x["case_id"]),
            file,
            indent=4,
            ensure_ascii=False
        )


def evaluate_all_cases():
    results = load_previous_results()

    print("Already successful:", len(results))

    for index, description in enumerate(NATURAL_LANGUAGE_CASES, start=1):

        if index in results:
            print(f"Case {index}: Already completed. Skipping.")
            continue

        print(f"\nProcessing case {index}/50...")

        for attempt in range(1, 4):
            start = time.perf_counter()

            try:
                response = ask_gemini(description)
                latency = time.perf_counter() - start

                results[index] = {
                    "case_id": index,
                    "description": description,
                    "response": response,
                    "latency_seconds": round(latency, 2),
                    "status": "success"
                }

                print(f"Success in {latency:.2f} seconds")
                break

            except Exception as error:
                print(f"Attempt {attempt} failed: {error}")

                if attempt < 3:
                    wait_time = 10 * attempt
                    print(f"Waiting {wait_time} seconds...")
                    time.sleep(wait_time)

                else:
                    results[index] = {
                        "case_id": index,
                        "description": description,
                        "response": None,
                        "latency_seconds": None,
                        "status": "failed",
                        "error": str(error)
                    }

            save_results(results)

        time.sleep(5)

    successful = sum(
        item["status"] == "success" for item in results.values()
    )

    failed = len(NATURAL_LANGUAGE_CASES) - successful

    print("\nEvaluation completed!")
    print("Total cases:", len(NATURAL_LANGUAGE_CASES))
    print("Successful:", successful)
    print("Failed:", failed)
    print("Success rate:", round(successful / len(NATURAL_LANGUAGE_CASES) * 100, 2), "%")
    print("Results saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    evaluate_all_cases()
