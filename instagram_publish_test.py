import os
import sys
import time
import requests

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")
IMAGE_URL = os.getenv("IMAGE_URL")
CAPTION = os.getenv("CAPTION", "SHARQ FX Market Update")
API_VERSION = os.getenv("INSTAGRAM_API_VERSION", "v22.0")

BASE_URL = f"https://graph.instagram.com/{API_VERSION}"


def require(name, value):
    if not value:
        raise RuntimeError(f"Missing required value: {name}")


def api_post(path, data):
    url = f"{BASE_URL}/{path.lstrip('/')}"
    response = requests.post(url, data=data, timeout=60)
    print(f"POST {path} -> HTTP {response.status_code}")

    if not response.ok:
        print(response.text)
        response.raise_for_status()

    return response.json()


def api_get(path, params):
    url = f"{BASE_URL}/{path.lstrip('/')}"
    response = requests.get(url, params=params, timeout=60)
    print(f"GET {path} -> HTTP {response.status_code}")

    if not response.ok:
        print(response.text)
        response.raise_for_status()

    return response.json()


def main():
    require("INSTAGRAM_ACCESS_TOKEN", ACCESS_TOKEN)
    require("INSTAGRAM_USER_ID", INSTAGRAM_USER_ID)
    require("IMAGE_URL", IMAGE_URL)

    print("SHARQ FX Instagram publish test")
    print("Image URL:", IMAGE_URL)
    print("Caption length:", len(CAPTION))

    create = api_post(
        f"{INSTAGRAM_USER_ID}/media",
        {
            "image_url": IMAGE_URL,
            "caption": CAPTION,
            "access_token": ACCESS_TOKEN,
        },
    )

    creation_id = create.get("id")
    if not creation_id:
        raise RuntimeError(f"No creation ID returned: {create}")

    print("Creation ID:", creation_id)

    status = None
    for attempt in range(12):
        status = api_get(
            creation_id,
            {
                "fields": "status_code,status",
                "access_token": ACCESS_TOKEN,
            },
        )

        status_code = status.get("status_code")
        print(
            f"Container status attempt {attempt + 1}: "
            f"{status_code} | {status.get('status')}"
        )

        if status_code == "FINISHED":
            break

        if status_code in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Container failed: {status}")

        time.sleep(5)
    else:
        raise RuntimeError(
            f"Container did not finish in time. Last status: {status}"
        )

    published = api_post(
        f"{INSTAGRAM_USER_ID}/media_publish",
        {
            "creation_id": creation_id,
            "access_token": ACCESS_TOKEN,
        },
    )

    media_id = published.get("id")
    if not media_id:
        raise RuntimeError(f"No published media ID returned: {published}")

    print("Instagram post published successfully")
    print("Published media ID:", media_id)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR:", exc)
        sys.exit(1)
