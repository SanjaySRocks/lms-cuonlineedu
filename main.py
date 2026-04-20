"""
CU Online LMS — Progress Automation CLI
========================================
Classes:
  - LMSClient      : all HTTP calls to the LMS (pedagogy) API
  - ProgressClient : all HTTP calls to the learner-progress API
  - CLI            : all user interaction and program flow
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ─── Constants ────────────────────────────────────────────────────────────────

LMS_BASE_URL      = "https://pedagogy.cuonlineedu.in/api/v1"
PROGRESS_BASE_URL = "https://learner-progress.cuonlineedu.in/api/v1"
PROGRAM_ID        = 75
BATCH_ID_FALLBACK = 839


# ─── LMS Client ───────────────────────────────────────────────────────────────

class LMSClient:
    """Handles all requests to the LMS (pedagogy) API."""

    def __init__(self):
        self.token            = None
        self.user_id          = None
        self.program_batch_id = None

    def _headers(self, with_auth=True, with_content_type=False):
        headers = {
            "accept" : "application/json, text/plain, */*",
            "origin" : "https://lms.cuonlineedu.in",
            "referer": "https://lms.cuonlineedu.in/",
        }
        if with_auth and self.token:
            headers["authorization"] = f"Bearer {self.token}"
        if with_content_type:
            headers["content-type"] = "application/json"
        return headers

    def login(self, username: str, password: str) -> bool:
        payload = {"username": username, "email": None, "password": password}
        try:
            resp = requests.post(
                f"{LMS_BASE_URL}/auth/login",
                json=payload,
                headers=self._headers(with_auth=False, with_content_type=True),
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            self.token = (
                data.get("token")
                or data.get("accessToken")
                or data.get("access_token")
            )
            self.user_id = (
                data.get("userId")
                or data.get("user_id")
                or (data.get("user") or {}).get("id")
                or (data.get("data") or {}).get("userId")
            )
            self.program_batch_id = (
                data.get("programBatchId")
                or (data.get("data") or {}).get("programBatchId")
                or BATCH_ID_FALLBACK
            )

            if not self.token:
                print(f"[ERROR] Could not extract token from response: {data}")
                return False

            return True

        except requests.exceptions.HTTPError:
            print(f"[ERROR] Login failed (HTTP {resp.status_code}): {resp.text}")
            return False
        except Exception as e:
            print(f"[ERROR] Login request failed: {e}")
            return False

    def get_subjects(self) -> list:
        url = (
            f"{LMS_BASE_URL}/users/subject/{PROGRAM_ID}"
            f"?programBatchId={self.program_batch_id}&userId={self.user_id}"
        )
        try:
            resp = requests.get(url, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else (
                data.get("data") or data.get("subjects") or data.get("result") or []
            )
        except requests.exceptions.HTTPError:
            print(f"[ERROR] Failed to fetch subjects (HTTP {resp.status_code}): {resp.text}")
            return []
        except Exception as e:
            print(f"[ERROR] Failed to fetch subjects: {e}")
            return []

    def get_modules(self, subject_id: int) -> list:
        url = f"{LMS_BASE_URL}/users/chapter/{subject_id}"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            data = resp.json()

            modules = data if isinstance(data, list) else (
                data.get("data") or data.get("chapters") or data.get("result") or []
            )

            # Filter out assessment modules
            filtered = [
                m for m in modules
                if not m.get("isAssessment", False)
                and not m.get("assessment", False)
                and not m.get("is_assessment", False)
            ]

            skipped = len(modules) - len(filtered)
            if skipped:
                print(f"  (Skipped {skipped} assessment module(s))")

            return filtered

        except requests.exceptions.HTTPError:
            print(f"[ERROR] Failed to fetch modules (HTTP {resp.status_code}): {resp.text}")
            return []
        except Exception as e:
            print(f"[ERROR] Failed to fetch modules: {e}")
            return []

    def get_content(self, module_id: int) -> list:
        url = f"{LMS_BASE_URL}/users/content/{module_id}"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else (
                data.get("data") or data.get("contents") or data.get("result") or []
            )
        except requests.exceptions.HTTPError:
            print(f"[ERROR] Failed to fetch content (HTTP {resp.status_code}): {resp.text}")
            return []
        except Exception as e:
            print(f"[ERROR] Failed to fetch content: {e}")
            return []


# ─── Progress Client ──────────────────────────────────────────────────────────

class ProgressClient:
    """Handles all requests to the learner-progress API."""

    def __init__(self, lms: LMSClient):
        self._lms = lms

    def _headers(self, with_content_type=False):
        headers = {
            "accept" : "application/json, text/plain, */*",
            "origin" : "https://lms.cuonlineedu.in",
            "referer": "https://lms.cuonlineedu.in/",
        }
        if self._lms.token:
            headers["authorization"] = f"Bearer {self._lms.token}"
        if with_content_type:
            headers["content-type"] = "application/json"
        return headers

    def get_content_progress(self, content_ids: list) -> dict:
        """Fetch progress for multiple content IDs in one batch request."""
        if not content_ids:
            return {}

        ids_param = ",".join(str(cid) for cid in content_ids)
        url = f"{PROGRESS_BASE_URL}/progress/content/{self._lms.user_id}?ids={ids_param}"

        try:
            resp = requests.get(url, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            data = resp.json()

            progress_map = {}
            items = data if isinstance(data, list) else (
                data.get("data") or data.get("result") or []
            )
            for item in items:
                cid  = item.get("contentId") or item.get("id")
                prog = item.get("progress", 0)
                if cid is not None:
                    progress_map[int(cid)] = prog

            return progress_map

        except Exception:
            return {}

    def mark_complete(self, content_id: int, chapter_id: int) -> tuple:
        payload = {
            "userId"   : self._lms.user_id,
            "contentId": content_id,
            "progress" : 100,
            "chapterId": chapter_id,
        }
        try:
            resp = requests.post(
                f"{PROGRESS_BASE_URL}/content-progress",
                json=payload,
                headers=self._headers(with_content_type=True),
                timeout=15,
            )
            resp.raise_for_status()
            return True, resp.status_code

        except requests.exceptions.HTTPError:
            return False, resp.status_code
        except Exception as e:
            return False, str(e)


# ─── CLI ──────────────────────────────────────────────────────────────────────

class CLI:
    """Handles all user interaction and program flow."""

    DIVIDER = "=" * 55

    def __init__(self, lms: LMSClient, progress: ProgressClient):
        self._lms      = lms
        self._progress = progress

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _progress_bar(pct: float) -> str:
        filled = int(pct / 10)
        bar    = "█" * filled + "░" * (10 - filled)
        return f"[{bar}] {int(pct):>3}%"

    def _pick_from_list(self, items: list, label_key: str, title: str):
        print(f"\n{self.DIVIDER}")
        print(f"  {title}")
        print(self.DIVIDER)

        if not items:
            print("  No items found.")
            return None

        for i, item in enumerate(items, 1):
            label = (
                item.get(label_key)
                or item.get("name")
                or item.get("title")
                or item.get("displayName")
                or f"Item {i}"
            )
            print(f"  [{i}] {label}")

        print(self.DIVIDER)

        while True:
            try:
                choice = int(input(f"Select (1-{len(items)}): "))
                if 1 <= choice <= len(items):
                    return items[choice - 1]
                print(f"  Please enter a number between 1 and {len(items)}.")
            except ValueError:
                print("  Invalid input. Enter a number.")

    # ── Auth ──────────────────────────────────────────────────────────────────

    def login(self):
        username = os.getenv("LMS_USERNAME")
        password = os.getenv("LMS_PASSWORD")

        if not username or not password:
            print("\n[ERROR] LMS_USERNAME or LMS_PASSWORD not found in .env file.")
            print("Create a .env file with:\n  LMS_USERNAME=your_username\n  LMS_PASSWORD=your_password")
            exit(1)

        print(f"\nLogging in as '{username}'...")

        if not self._lms.login(username, password):
            exit(1)

        print(f"Login successful! userId={self._lms.user_id}, programBatchId={self._lms.program_batch_id}")

    # ── Module processing ─────────────────────────────────────────────────────

    def process_module(self, module: dict):
        module_id   = module.get("id") or module.get("chapterId")
        module_name = module.get("name") or module.get("title") or f"Module {module_id}"
        chapter_id  = module_id

        print(f"\nFetching content for module: {module_name}...")
        contents = self._lms.get_content(module_id)

        if not contents:
            print("  No video content found in this module.")
            return

        content_ids = [
            c.get("id") or c.get("contentId")
            for c in contents
            if c.get("id") or c.get("contentId")
        ]

        print(f"  Fetching progress for {len(content_ids)} item(s)...", end="", flush=True)
        progress_map = self._progress.get_content_progress(content_ids)
        print(" done.")

        # Display content list with progress bars
        print(f"\n  {'#':<4} {'Progress':<20} Title")
        print(f"  {'-'*4} {'-'*20} {'-'*32}")
        for i, c in enumerate(contents, 1):
            cid  = c.get("id") or c.get("contentId")
            name = c.get("name") or c.get("title") or c.get("contentName") or f"Content {i}"
            pct  = progress_map.get(int(cid), 0) if cid else 0
            print(f"  {i:<4} {self._progress_bar(pct)}  {name}")

        # Summary
        completed = sum(1 for cid in content_ids if progress_map.get(int(cid), 0) >= 100)
        print(f"\n  Completed: {completed}/{len(contents)}")

        if completed == len(contents):
            print("  All videos already marked complete!")
            if input("  Mark them all again anyway? (y/n): ").strip().lower() != "y":
                return

        print("\n  [1] Mark ALL as 100% complete")
        print("  [2] Mark one by one")

        while True:
            mode = input("Choose option (1 or 2): ").strip()
            if mode in ("1", "2"):
                break
            print("  Please enter 1 or 2.")

        for i, content in enumerate(contents, 1):
            content_id  = content.get("id") or content.get("contentId")
            name        = content.get("name") or content.get("title") or content.get("contentName") or f"Content {i}"
            current_pct = progress_map.get(int(content_id), 0) if content_id else 0

            if mode == "2":
                already = " ✓ already 100%" if current_pct >= 100 else f" ({int(current_pct)}%)"
                confirm = input(f"\n  [{i}] '{name}'{already} — mark complete? (y/n): ").strip().lower()
                if confirm != "y":
                    print("  Skipped.")
                    continue

            print(f"  Marking '{name}'... ", end="", flush=True)
            success, status = self._progress.mark_complete(content_id, chapter_id)
            print("Done ✓" if success else f"Failed ✗ (status: {status})")

            if mode == "1" and i < len(contents):
                time.sleep(1.5)

    # ── Main flow ─────────────────────────────────────────────────────────────

    def run(self):
        print("\n" + self.DIVIDER)
        print("   CU Online LMS — Progress Automation CLI")
        print(self.DIVIDER)

        self.login()

        while True:
            print("\nFetching your subjects...")
            subjects = self._lms.get_subjects()

            subject = self._pick_from_list(subjects, "subjectName", "Select a Subject")
            if not subject:
                print("No subjects available. Exiting.")
                break

            subject_id   = subject.get("id") or subject.get("subjectId")
            subject_name = subject.get("subjectName") or subject.get("name") or f"Subject {subject_id}"
            print(f"\nSelected subject: {subject_name}")

            while True:
                print("\nFetching modules...")
                modules = self._lms.get_modules(subject_id)

                module = self._pick_from_list(modules, "chapterName", "Select a Module")
                if not module:
                    print("No modules available.")
                    break

                module_name = module.get("chapterName") or module.get("name") or "Selected Module"
                print(f"Selected module: {module_name}")

                self.process_module(module)

                if input("\nDo you want to continue with another module? (y/n): ").strip().lower() != "y":
                    break

            if input("\nDo you want to switch to a different subject? (y/n): ").strip().lower() != "y":
                print("\nAll done! Exiting.")
                break


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    lms      = LMSClient()
    progress = ProgressClient(lms)
    cli      = CLI(lms, progress)
    cli.run()


if __name__ == "__main__":
    main()
