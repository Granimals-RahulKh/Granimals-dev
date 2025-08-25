import json
import os
import base64
import boto3
import logging
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cache secrets for warm starts
_cached_api_key = None

def get_openai_key():
    global _cached_api_key
    if _cached_api_key:
        return _cached_api_key

    secret_name = os.environ.get("OPENAI_SECRET_NAME", "openai_key")
    region = os.environ.get("AWS_REGION", "ap-south-1")

    client = boto3.client("secretsmanager", region_name=region)
    resp = client.get_secret_value(SecretId=secret_name)

    if "SecretString" in resp:
        val = resp["SecretString"]
        try:
            data = json.loads(val)
            _cached_api_key = (
                data.get("OPENAI_API_KEY")
                or data.get("openai_api_key")
                or data.get("api_key")
            )
        except Exception:
            _cached_api_key = val
    else:
        _cached_api_key = base64.b64decode(resp["SecretBinary"]).decode("utf-8")

    return _cached_api_key

def safe_json_extract(content: str):
    """Extract valid JSON even if wrapped in markdown fences."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Strip markdown ```json fences if present
        if content.strip().startswith("```"):
            cleaned = "\n".join(
                line for line in content.splitlines()
                if not line.strip().startswith("```")
            )
            try:
                return json.loads(cleaned)
            except Exception:
                pass
        # Last fallback → wrap into result
        return {"result": content, "details": {"warning": "Model did not return strict JSON"}}

def call_chatgpt(prompt, inputs):
    """
    Generic HTTPS call to OpenAI Chat Completions/Responses style.
    """
    api_key = get_openai_key()
    api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    url = f"{api_base}/chat/completions"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a strict JSON API."},
            {
                "role": "user",
                "content": (
                    f"Inputs:\n"
                    f"input1: {inputs['input1']}\n"
                    f"input2: {inputs['input2']}\n"
                    f"input3: {inputs['input3']}\n"
                    f"Task: {prompt}\n"
                ),
            },
        ],
        "temperature": 0.2,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        return safe_json_extract(content)

def parse_event(event):
    if event.get("isBase64Encoded"):
        body = base64.b64decode(event.get("body") or "").decode("utf-8")
    else:
        body = event.get("body") or ""
    try:
        return json.loads(body)
    except Exception:
        return {}

def response(status, body, origin):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Headers": "content-type,authorization",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(body),
    }

def lambda_handler(event, context):
    logger.info({"event": event.get("requestContext", {})})
    origin = os.environ.get("FRONTEND_ORIGIN", "*")

    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return response(200, {"ok": True}, origin)

    payload = parse_event(event)
    input1 = payload.get("input1")
    input2 = payload.get("input2")
    input3 = payload.get("input3")

    missing = [k for k, v in {"input1": input1, "input2": input2, "input3": input3}.items() if v is None]
    if missing:
        return response(400, {"error": f"Missing fields: {', '.join(missing)}"}, origin)

    # Nutrition prompt
    prompt = (
        "You are a nutrition assistant for Granimals. "
        "Given a food item and its quantity, return the estimated nutritional values "
        "in JSON format only. Do not include any extra fields.\n\n"
        f"Food item: {input1}\n"
        f"Quantity: {input2} {input3}\n\n"
        "Respond strictly as:\n"
        "{\n"
        "  \"calories\": <number>,\n"
        "  \"carbs\": <number>,\n"
        "  \"fats\": <number>,\n"
        "  \"proteins\": <number>,\n"
        "  \"fibre\": <number>\n"
        "}"
    )

    try:
        result = call_chatgpt(prompt, {"input1": input1, "input2": input2, "input3": input3})
        return response(200, result, origin)
    except Exception as e:
        logger.exception("chatgpt_call_failed")
        return response(502, {"ok": False, "error": str(e)}, origin)
