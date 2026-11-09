
import time
import pytest
from project_a.implementations.llm_based import ask_gemini


@pytest.mark.integration
def test_llm_latency_and_determinism():
    description = """
    My annual salary is 12 lakh.
    I am 25 years old and a resident of India.
    I have no investments or health insurance.
    """

    responses = []
    latencies = []

    for i in range(10):
        try:
            start = time.perf_counter()
            result = ask_gemini(description)
            elapsed = time.perf_counter() - start

            responses.append(result)
            latencies.append(elapsed)

            print(f"Request {i + 1}: {elapsed:.2f} seconds")

        except Exception as error:
            pytest.fail(f"Gemini request {i + 1} failed: {error}")

    identical = all(
        result == responses[0] for result in responses
    )

    print("\nAverage latency:", round(sum(latencies) / len(latencies), 2))
    print("Minimum latency:", round(min(latencies), 2))
    print("Maximum latency:", round(max(latencies), 2))
    print("Identical responses:", identical)



import time
import pytest
from project_a.implementations.llm_based import ask_gemini


@pytest.mark.integration
def test_llm_latency_and_determinism():
    description = """
    My annual salary is 12 lakh.
    I am 25 years old and a resident of India.
    I have no investments or health insurance.
    """

    responses = []
    latencies = []

    for i in range(10):
        try:
            start = time.perf_counter()
            result = ask_gemini(description)
            elapsed = time.perf_counter() - start

            responses.append(result)
            latencies.append(elapsed)

            print(f"Request {i + 1}: {elapsed:.2f} seconds")

        except Exception as error:
            pytest.fail(f"Gemini request {i + 1} failed: {error}")

    identical = all(
        result == responses[0] for result in responses
    )

    print("\nAverage latency:", round(sum(latencies) / len(latencies), 2))
    print("Minimum latency:", round(min(latencies), 2))
    print("Maximum latency:", round(max(latencies), 2))
    print("Identical responses:", identical)


