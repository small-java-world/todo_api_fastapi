import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class GitService:
    def __init__(self):
        self.git_root = settings.get_git_repo_path()
        self.git_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"Git root path: {self.git_root}")

    def get_task_path(self, hierarchical_id: str) -> Path:
        """タスクのGitパスを取得"""
        parts = hierarchical_id.split(".")
        if len(parts) == 1:  # REQ-001
            return self.git_root / "requirements" / parts[0]
        elif len(parts) == 2:  # REQ-001.TSK-001
            return self.git_root / "requirements" / parts[0] / "tasks" / parts[1]
        elif len(parts) == 3:  # REQ-001.TSK-001.SUB-001
            return (
                self.git_root
                / "requirements"
                / parts[0]
                / "tasks"
                / parts[1]
                / "subtasks"
                / parts[2]
            )
        else:
            raise ValueError(f"Invalid hierarchical ID: {hierarchical_id}")

    def get_outline_path(self, hierarchical_id: str) -> Path:
        """アウトラインJSONファイルのパスを取得"""
        task_path = self.get_task_path(hierarchical_id)
        return task_path / "outline.json"

    def get_spec_path(self, hierarchical_id: str) -> Path:
        """仕様ファイルのパスを取得"""
        task_path = self.get_task_path(hierarchical_id)
        if hierarchical_id.startswith("REQ-"):
            return task_path / "requirement.md"
        elif ".TSK-" in hierarchical_id:
            return task_path / "task.md"
        elif ".SUB-" in hierarchical_id:
            return task_path / "subtask.md"
        else:
            raise ValueError(f"Invalid hierarchical ID: {hierarchical_id}")

    def get_tests_path(self, hierarchical_id: str) -> Path:
        """テストディレクトリのパスを取得"""
        if ".TSK-" in hierarchical_id:
            task_path = self.get_task_path(hierarchical_id)
            return task_path / "tests"
        else:
            raise ValueError(
                f"Tests path only available for tasks, not: {hierarchical_id}"
            )

    def create_outline_file(
        self, hierarchical_id: str, outline_data: Dict[str, Any]
    ) -> bool:
        """アウトラインJSONファイルを作成"""
        try:
            outline_path = self.get_outline_path(hierarchical_id)
            outline_path.parent.mkdir(parents=True, exist_ok=True)

            import json

            with open(outline_path, "w", encoding="utf-8") as f:
                json.dump(outline_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Created outline file: {outline_path}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to create outline file for {hierarchical_id}: {str(e)}"
            )
            return False

    def get_outline_file(self, hierarchical_id: str) -> Optional[Dict[str, Any]]:
        """アウトラインJSONファイルを取得"""
        try:
            outline_path = self.get_outline_path(hierarchical_id)
            if not outline_path.exists():
                return None

            import json

            with open(outline_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read outline file for {hierarchical_id}: {str(e)}")
            return None

    def create_spec_file(self, hierarchical_id: str, content: str) -> bool:
        """仕様ファイルを作成"""
        try:
            spec_path = self.get_spec_path(hierarchical_id)
            spec_path.parent.mkdir(parents=True, exist_ok=True)

            with open(spec_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Created spec file: {spec_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create spec file for {hierarchical_id}: {str(e)}")
            return False

    def get_spec_file(self, hierarchical_id: str) -> Optional[str]:
        """仕様ファイルを取得"""
        try:
            spec_path = self.get_spec_path(hierarchical_id)
            if not spec_path.exists():
                return None

            with open(spec_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read spec file for {hierarchical_id}: {str(e)}")
            return None

    def get_git_uri(self, hierarchical_id: str, file_type: str = "outline") -> str:
        """Git URIを生成"""
        if file_type == "outline":
            file_path = self.get_outline_path(hierarchical_id)
        elif file_type == "spec":
            file_path = self.get_spec_path(hierarchical_id)
        elif file_type == "tests":
            file_path = self.get_tests_path(hierarchical_id)
        else:
            raise ValueError(f"Invalid file type: {file_type}")

        # 相対パスを取得
        relative_path = file_path.relative_to(self.git_root)
        return f"git://{relative_path.as_posix()}"

    def list_task_files(self, hierarchical_id: str) -> List[Dict[str, str]]:
        """タスクに関連するファイル一覧を取得"""
        try:
            task_path = self.get_task_path(hierarchical_id)
            if not task_path.exists():
                return []

            files = []
            for file_path in task_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.git_root)
                    files.append(
                        {
                            "name": file_path.name,
                            "path": str(relative_path),
                            "uri": f"git://{relative_path.as_posix()}",
                            "type": file_path.suffix[1:] if file_path.suffix else "txt",
                        }
                    )

            return files
        except Exception as e:
            logger.error(f"Failed to list files for {hierarchical_id}: {str(e)}")
            return []

    def initialize_git_repo(self) -> bool:
        """Gitリポジトリを初期化"""
        try:
            if not (self.git_root / ".git").exists():
                subprocess.run(["git", "init"], cwd=self.git_root, check=True)
                logger.info(f"Initialized git repository at {self.git_root}")

            # .gitignoreファイルを作成
            gitignore_path = self.git_root / ".gitignore"
            if not gitignore_path.exists():
                with open(gitignore_path, "w") as f:
                    f.write("# Ignore temporary files\n*.tmp\n*.log\n")

            return True
        except Exception as e:
            logger.error(f"Failed to initialize git repository: {str(e)}")
            return False

    def commit_changes(self, message: str) -> bool:
        """変更をコミット"""
        try:
            # 全てのファイルを追加
            subprocess.run(["git", "add", "."], cwd=self.git_root, check=True)

            # コミット
            subprocess.run(
                ["git", "commit", "-m", message], cwd=self.git_root, check=True
            )

            logger.info(f"Committed changes: {message}")
            return True
        except subprocess.CalledProcessError:
            # コミットする変更がない場合
            logger.info("No changes to commit")
            return True
        except Exception as e:
            logger.error(f"Failed to commit changes: {str(e)}")
            return False
