import os
import time
import base64
import logging
import json
import requests
from pathlib import Path
from typing import Dict, Any

import pymupdf  # Replaces deprecated fitz

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import the robust schema prompt builder
from schema import create_extraction_prompt

# Enable CORS for React Frontend


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class LiftModelClient:
    def __init__(self, endpoint_url: str = "http://localhost:8000/v1"):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.name = "/home/ubuntu/models/lift"

        # Reuse the same HTTP connection instead of creating a new
        # TCP connection for every PDF request.
        self.session = requests.Session()

        # Keep connections alive and avoid unnecessary HTTP overhead.
        self.session.headers.update({
            "Connection": "keep-alive"
        })

        logger.info(
            f"Initializing Lift HTTP Client with Schema Prompts "
            f"(vLLM at {self.endpoint_url})"
        )

    def extract_from_pdf(
        self,
        pdf_path: Path,
        schema: dict
    ) -> Dict[str, Any]:

        start = time.perf_counter()

        try:
            doc = pymupdf.open(pdf_path)
            image_content_blocks = []

            max_pages = len(doc)

            logger.info(
                f"Processing all {max_pages} pages for {pdf_path.name}"
            )

            # ---------------------------------------------------------
            # PDF -> PNG -> Base64
            # ---------------------------------------------------------
            #
            # Important optimisation:
            #
            # pix.tobytes("png") already gives us PNG bytes.
            # There is no need to:
            #
            # PNG -> PIL Image -> BytesIO -> PNG
            #
            # This removes an unnecessary decode/re-encode operation.
            #
            for page_num in range(max_pages):
                page = doc.load_page(page_num)

                # Keep 85 DPI to preserve the existing benchmark behaviour.
                pix = page.get_pixmap(
                    dpi=85,
                    alpha=False
                )

                png_bytes = pix.tobytes("png")

                img_base64 = base64.b64encode(
                    png_bytes
                ).decode("ascii")

                image_content_blocks.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_base64}"
                    }
                })

            # Explicitly close the PDF as soon as rendering is finished.
            doc.close()

        except Exception as e:
            logger.error(
                f"Failed to convert PDF {pdf_path.name} to images: {e}"
            )

            return {
                "model": self.name,
                "response": None,
                "latency_seconds": time.perf_counter() - start,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "error": str(e)
            }

        # -------------------------------------------------------------
        # Prompt
        # -------------------------------------------------------------

        prompt_text = create_extraction_prompt(
            rfp_text="[All PDF Document Pages Provided via Image Blocks]"
        )

        messages_content = [
            {
                "type": "text",
                "text": prompt_text
            }
        ]

        messages_content.extend(image_content_blocks)

        # -------------------------------------------------------------
        # Request payload
        # -------------------------------------------------------------

        payload = {
            "model": self.name,
            "messages": [
                {
                    "role": "user",
                    "content": messages_content
                }
            ],
            "response_format": {
                "type": "json_object"
            },
            "max_tokens": 4096,
            "temperature": 0.0
        }

        # -------------------------------------------------------------
        # vLLM request
        # -------------------------------------------------------------

        try:
            response = self.session.post(
                f"{self.endpoint_url}/chat/completions",
                json=payload,
                timeout=(10, 300)
            )

            if response.status_code != 200:
                logger.error(
                    f"vLLM Error Response "
                    f"({response.status_code}): {response.text}"
                )

            response.raise_for_status()

            data = response.json()

            # ---------------------------------------------------------
            # Parse model response
            # ---------------------------------------------------------

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            if isinstance(content, str):
                parsed_content = json.loads(content)
            else:
                parsed_content = content

            end = time.perf_counter()

            return {
                "model": self.name,
                "response": parsed_content,
                "latency_seconds": end - start,
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "error": None
            }

        except Exception as e:
            end = time.perf_counter()

            logger.error(
                f"Error during Lift HTTP extraction for "
                f"{pdf_path.name}: {str(e)}"
            )

            return {
                "model": self.name,
                "response": None,
                "latency_seconds": end - start,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "error": str(e)
            }
