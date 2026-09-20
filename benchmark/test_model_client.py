from model_client import ModelClient


client = ModelClient(
    name="Qwen2.5-32B-Instruct-AWQ",
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",
    model="/home/ubuntu/models/Qwen2.5-32B-Instruct-AWQ"
)


result = client.generate(
    "What is an RFP? Answer in one sentence."
)


print("Model:")
print(result["model"])

print()

print("Response:")
print(result["response"])

print()

print("Latency:")
print(result["latency_seconds"])

print()

print("Input tokens:")
print(result["input_tokens"])

print()

print("Output tokens:")
print(result["output_tokens"])

print()

print("Total tokens:")
print(result["total_tokens"])