"""
Skyvern Client with Ollama Integration

Provides a configured Skyvern client for browser automation
using local Ollama models.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from backend.app.config import settings

logger = logging.getLogger(__name__)


class SkyvernClient:
    """
    Wrapper for Skyvern API with Ollama configuration.

    This client handles the integration between Skyvern and local Ollama
    for cost-free browser automation.
    """

    def __init__(self):
        """Initialize Skyvern client with Ollama configuration."""
        self.enabled = settings.enable_skyvern
        self.ollama_enabled = settings.enable_ollama
        self.ollama_url = settings.ollama_server_url
        self.model = settings.skyvern_ollama_model

        if not self.enabled:
            logger.warning("Skyvern is disabled. Enable it in .env with ENABLE_SKYVERN=true")
            return

        # Set environment variables for Skyvern
        if self.ollama_enabled:
            os.environ["ENABLE_OLLAMA"] = "true"
            os.environ["OLLAMA_SERVER_URL"] = self.ollama_url
            os.environ["OLLAMA_MODEL"] = self.model
            logger.info(f"Skyvern configured with Ollama: {self.model}")

        try:
            # Import skyvern only if enabled
            from skyvern import Skyvern
            self.skyvern = Skyvern()
            logger.info("Skyvern client initialized successfully")
        except ImportError:
            logger.error(
                "Skyvern not installed. Install with: pip install skyvern"
            )
            self.skyvern = None
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Skyvern: {str(e)}")
            self.skyvern = None
            self.enabled = False

    async def run_task(
        self,
        url: str,
        prompt: str,
        navigation_goal: Optional[str] = None,
        data_extraction_goal: Optional[str] = None,
        max_steps: int = 10
    ) -> Dict[str, Any]:
        """
        Run a Skyvern task with the given parameters.

        Args:
            url: Starting URL for the task
            prompt: Main instruction prompt for Skyvern
            navigation_goal: Optional specific navigation instructions
            data_extraction_goal: Optional specific data extraction instructions
            max_steps: Maximum number of steps before timeout

        Returns:
            Dictionary with task results and extracted data

        Raises:
            RuntimeError: If Skyvern is not enabled or initialized
        """
        if not self.enabled or not self.skyvern:
            raise RuntimeError(
                "Skyvern is not enabled. Check configuration and installation."
            )

        try:
            logger.info(f"Starting Skyvern task on {url}")

            # Combine goals into the prompt if provided
            full_prompt = prompt
            if navigation_goal:
                full_prompt += f"\n\nNavigation: {navigation_goal}"
            if data_extraction_goal:
                full_prompt += f"\n\nExtract: {data_extraction_goal}"

            # Run the task
            task = await self.skyvern.run_task(
                url=url,
                prompt=full_prompt,
                max_steps=max_steps
            )

            logger.info(f"Task completed with status: {task.status}")

            return {
                "status": task.status,
                "extracted_data": task.extracted_data,
                "failure_reason": getattr(task, "failure_reason", None),
            }

        except Exception as e:
            logger.error(f"Skyvern task failed: {str(e)}")
            return {
                "status": "failed",
                "extracted_data": None,
                "failure_reason": str(e),
            }

    async def extract_data(
        self,
        url: str,
        extraction_schema: Dict[str, str],
        navigation_steps: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Extract structured data from a webpage.

        Args:
            url: URL to extract data from
            extraction_schema: Dictionary mapping field names to descriptions
                Example: {
                    "title": "Novel title",
                    "author": "Author name",
                    "description": "Brief description or synopsis"
                }
            navigation_steps: Optional list of navigation steps to perform first

        Returns:
            List of extracted data dictionaries matching the schema
        """
        if not self.enabled:
            raise RuntimeError("Skyvern is not enabled")

        # Build extraction prompt
        schema_desc = "\n".join([
            f"- {key}: {desc}"
            for key, desc in extraction_schema.items()
        ])

        prompt = f"""
        Extract the following information from all items on this page:
        {schema_desc}

        Return the data as a structured list.
        """

        if navigation_steps:
            nav_desc = "\n".join([f"{i+1}. {step}" for i, step in enumerate(navigation_steps)])
            prompt = f"First:\n{nav_desc}\n\nThen:\n{prompt}"

        result = await self.run_task(
            url=url,
            prompt=prompt,
            data_extraction_goal=schema_desc
        )

        if result["status"] == "completed":
            return result.get("extracted_data", [])
        else:
            logger.error(f"Data extraction failed: {result.get('failure_reason')}")
            return []

    async def login_to_site(
        self,
        url: str,
        username: str,
        password: str,
        username_field_desc: str = "username or email input field",
        password_field_desc: str = "password input field",
        login_button_desc: str = "login button"
    ) -> bool:
        """
        Login to a website using Skyvern.

        Args:
            url: Login page URL
            username: Username or email
            password: Password
            username_field_desc: Description of username field
            password_field_desc: Description of password field
            login_button_desc: Description of login button

        Returns:
            True if login successful, False otherwise
        """
        if not self.enabled:
            raise RuntimeError("Skyvern is not enabled")

        prompt = f"""
        Login to this website:
        1. Find the {username_field_desc} and enter: {username}
        2. Find the {password_field_desc} and enter: {password}
        3. Click the {login_button_desc}
        4. Wait for the page to load after login
        """

        result = await self.run_task(
            url=url,
            prompt=prompt,
            navigation_goal="Complete the login process"
        )

        success = result["status"] == "completed"

        if success:
            logger.info(f"Login successful for {username}")
        else:
            logger.error(f"Login failed: {result.get('failure_reason')}")

        return success

    def is_available(self) -> bool:
        """Check if Skyvern client is available and ready."""
        return self.enabled and self.skyvern is not None
