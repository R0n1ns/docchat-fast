import mimetypes
import os

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

    # def upload_document(self, file_path: str, title: str) -> Dict:
    #     with open(file_path, 'rb') as f:
    #         files = {'file': (title, f)}
    #         response = self.session.post(
    #             f"{self.base_url}/api/v1/documents?title={title}",
    #             files=files,
    #             headers={"Authorization": f"Bearer {self.access_token}"}
    #         )
    #     return self._handle_response(response)

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

    def upload_document(self, file_path: str, title: str) -> Dict:
        # Определяем MIME-тип файла
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'

        # Получаем имя файла из пути
        filename = os.path.basename(file_path)

        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, content_type)}
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            response = self.session.post(
                f"{self.base_url}/api/v1/documents?title={title}",
                files=files,
                headers=headers
            )
        return self._handle_response(response)

    def download_document(self, document_id: int) -> bytes:
        response = self.session.get(
            f"{self.base_url}/api/v1/documents/{document_id}/download",
            headers=self._get_headers()
        )
        try:
            response.raise_for_status()
            return response.content
        except requests.exceptions.HTTPError as e:
            raise APIError(f"Download failed: {str(e)}", response.status_code)

    def verify_document_integrity(self, document_id: int) -> dict:
        response = self.session.get(
            f"{self.base_url}/api/v1/documents/{document_id}/verify",
            headers=self._get_headers()
        )
        return self._handle_response(response)

    def update_document_metadata(self, document_id: int, metadata: dict) -> dict:
        response = self.session.patch(
            f"{self.base_url}/api/v1/documents/{document_id}",
            json=metadata,
            headers=self._get_headers()
        )
        return self._handle_response(response)

    def delete_document(self, document_id: int) -> dict:
        response = self.session.delete(
            f"{self.base_url}/api/v1/documents/delete/{document_id}",
            headers=self._get_headers()
        )
        return self._handle_response(response)

    def logout(self) -> None:
        if self.refresh_token:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/logout",
                json={"refresh_token": self.refresh_token},
                headers=self._get_headers()
            )
            self._handle_response(response)

    def upload_new_version(self, document_id: int, file_path: str) -> dict:
        # Определяем MIME-тип файла
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'

        # Получаем имя файла из пути
        filename = os.path.basename(file_path)

        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, content_type)}
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            response = self.session.post(
                f"{self.base_url}/api/v1/documents/{document_id}/upload",
                files=files,
                headers=headers
            )
        return self._handle_response(response)

    def get_document(self, document_id: int) -> dict:
        response = self.session.get(
            f"{self.base_url}/api/v1/documents/{document_id}",
            headers=self._get_headers()
        )
        return self._handle_response(response)

    def get_users(self) -> List[Dict]:
        """Получить список пользователей"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/users",
                headers=self._get_headers()
            )
            return self._handle_response(response)
        except APIError:
            return []  # Возвращаем пустой список при ошибке

    def share_document(self, document_id: int, user_ids: List[int], group_ids: List[int], notes: str = "") -> dict:
        """Отправить документ пользователям и группам"""
        # Отправка пользователям
        for user_id in user_ids:
            payload = {
                "user_id": user_id,
                "access_level": "view"  # Или другой уровень доступа
            }
            response = self.session.post(
                f"{self.base_url}/api/v1/documents/{document_id}/share",
                json=payload,
                headers=self._get_headers()
            )
            self._handle_response(response)

        # Отправка группам (если реализовано в API)
        # for group_id in group_ids:
        #     payload = {
        #         "group_id": group_id,
        #         "access_level": "view"
        #     }
        #     response = self.session.post(
        #         f"{self.base_url}/api/v1/documents/{document_id}/share-group",
        #         json=payload,
        #         headers=self._get_headers()
        #     )
        #     self._handle_response(response)

        # Возвращаем результат последней операции
        return {"status": "success"}

    def get_groups(self) -> List[Dict]:
        """Получить список групп"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/groups",
                headers=self._get_headers()
            )
            return self._handle_response(response)
        except APIError:
            return []

    def create_group(self, name: str, leader_id: int) -> Dict:
        """Создать новую группу"""
        group_data = {
            "name": name,
            "leader_id": leader_id
        }
        response = self.session.post(
            f"{self.base_url}/api/v1/groups",
            json=group_data,
            headers=self._get_headers()
        )
        return self._handle_response(response)

    def update_user(self, user_id: int, **kwargs) -> Dict:
        """Обновить данные пользователя"""
        # Формируем данные для обновления
        user_data = {}
        if "email" in kwargs:
            user_data["email"] = kwargs["email"]
        if "full_name" in kwargs:
            user_data["full_name"] = kwargs["full_name"]
        if "job_title" in kwargs:
            user_data["job_title"] = kwargs["job_title"]
        if "role" in kwargs:
            user_data["role"] = kwargs["role"]
        if "is_active" in kwargs:
            user_data["is_active"] = kwargs["is_active"]

        response = self.session.patch(
            f"{self.base_url}/api/v1/users/{user_id}",
            json=user_data,
            headers=self._get_headers()
        )
        return self._handle_response(response)