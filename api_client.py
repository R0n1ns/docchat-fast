import requests
from typing import Optional, Dict, List, Any

from PyQt6.QtCore import QSettings
from requests.exceptions import RequestException
import json
from datetime import datetime, timedelta


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class APIClient:
    def __init__(self, base_url: str = None):
        self.settings = QSettings("YourCompany", "EDI_System")
        self.base_url = base_url or self.settings.value("server_url", "")
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.access_token and self.token_expires > datetime.now():
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _handle_response(self, response):
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = response.json().get("detail", str(e)) if response.content else str(e)
            raise APIError(error_msg, response.status_code)
        except json.JSONDecodeError:
            raise APIError("Invalid JSON response")
        except Exception as e:
            raise APIError(str(e))

    # Authentication methods
    def login_init(self, email: str, password: str) -> Dict:
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login-init",
            data={"username": email, "password": password}
        )
        return self._handle_response(response)

    def login(self, email: str, totp_code: str) -> Dict:
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "totp_code": totp_code}
        )
        data = self._handle_response(response)
        self._update_tokens(data)
        return data

    def refresh_access_token(self) -> None:
        if not self.refresh_token:
            raise APIError("No refresh token available")

        response = self.session.post(
            f"{self.base_url}/api/v1/auth/refresh-token",
            json={"refresh_token": self.refresh_token}
        )
        data = self._handle_response(response)
        self._update_tokens(data)

    def _update_tokens(self, token_data: Dict) -> None:
        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")
        self.token_expires = datetime.now() + timedelta(minutes=55)

    # User methods
    def get_current_user(self) -> Dict:
        response = self.session.get(
            f"{self.base_url}/api/v1/users/me",
            headers=self._get_headers()
        )
        return self._handle_response(response)

    def get_users(self, search_query: Optional[str] = None) -> List[Dict]:
        params = {"search": search_query} if search_query else {}
        response = self.session.get(
            f"{self.base_url}/api/v1/users",
            headers=self._get_headers(),
            params=params
        )
        return self._handle_response(response)

    def create_user(self, email: str, password: str, role: str) -> Dict:
        user_data = {
            "email": email,
            "password": password,
            "role": role,
            "is_active": True
        }
        response = self.session.post(
            f"{self.base_url}/api/v1/users",
            json=user_data,
            headers=self._get_headers()
        )
        return self._handle_response(response)

    # Document methods
    def get_documents(self, status: str = None) -> List[Dict]:
        params = {"status": status} if status else {}
        response = self.session.get(
            f"{self.base_url}/api/v1/documents",
            headers=self._get_headers(),
            params=params
        )
        return self._handle_response(response)

    def upload_document(self, file_path: str, title: str) -> Dict:
        with open(file_path, 'rb') as f:
            files = {'file': (title, f)}
            response = self.session.post(
                f"{self.base_url}/api/v1/documents?title={title}",
                files=files,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
        return self._handle_response(response)

    def check_health(self) -> bool:
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/system/health",
                timeout=5
            )
            return response.status_code == 200
        except (RequestException, ConnectionError):
            return False
    def update_base_url(self,server_url):
        self.base_url = server_url