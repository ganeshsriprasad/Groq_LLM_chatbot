import httpx
import os
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class GrokClient:
    def __init__(self):
        self.api_key = os.getenv("GROK_API_KEY")
        self.base_url = os.getenv("GROK_API_BASE", "https://api.x.ai/v1")
        
        if not self.api_key:
            raise ValueError("GROK_API_KEY environment variable is required")
    
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a response using Grok API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Generated response string
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": messages,
            "model": "llama-3.1-8b-instant",
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            # First try with SSL verification
            async with httpx.AsyncClient(
                timeout=30.0,
                verify=True,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            ) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    raise Exception("No response from Grok API")
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Grok API: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API request failed: {e.response.status_code}")
        except httpx.ConnectError as e:
            # If SSL verification fails, try without verification
            if "CERTIFICATE_VERIFY_FAILED" in str(e):
                logger.warning("SSL verification failed, trying without SSL verification...")
                try:
                    async with httpx.AsyncClient(
                        timeout=30.0,
                        verify=False,  # Disable SSL verification
                        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                    ) as client:
                        response = await client.post(
                            f"{self.base_url}/chat/completions",
                            headers=headers,
                            json=payload
                        )
                        
                        response.raise_for_status()
                        data = response.json()
                        
                        if "choices" in data and len(data["choices"]) > 0:
                            return data["choices"][0]["message"]["content"]
                        else:
                            raise Exception("No response from Grok API")
                except Exception as fallback_error:
                    logger.error(f"Fallback request also failed: {fallback_error}")
                    raise Exception(f"Connection failed even without SSL verification: {str(fallback_error)}")
            else:
                logger.error(f"Connection error: {str(e)}")
                raise Exception(f"Connection failed: {str(e)}")
        except httpx.TimeoutException:
            logger.error("Timeout while calling Grok API")
            raise Exception("Request timeout - please try again")
        except Exception as e:
            logger.error(f"Error calling Grok API: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test if the API connection is working"""
        try:
            test_messages = [{"role": "user", "content": "Hello"}]
            await self.generate_response(test_messages)
            return True
        except Exception:
            return False
