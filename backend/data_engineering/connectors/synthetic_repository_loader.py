from typing import Any

from data_engineering.schemas.source_schema import SourceRecord


class SyntheticRepositoryLoader:
    """
    Converts generated synthetic repository data into
    standardized HandoverOS SourceRecord objects.

    No external repository, API, token or authentication
    is required.
    """

    def __init__(self):
        self.source_type = "synthetic"

    def load(self, repository_data: dict[str, Any]) -> list[SourceRecord]:
        """
        Convert all supported repository data into SourceRecords.
        """

        if not isinstance(repository_data, dict):
            raise TypeError("Repository data must be a dictionary.")

        repository = repository_data.get("repository")

        if not isinstance(repository, dict):
            raise ValueError("Repository metadata is missing.")

        project_id = repository.get("repository_id")

        if not project_id:
            raise ValueError("Repository ID is missing.")

        records = []

        # Repository metadata
        records.append(
            self._create_record(
                project_id=project_id,
                source_name="Synthetic Repository",
                source_id=project_id,
                title=repository.get("name", "Unknown Repository"),
                content=repository.get("description", ""),
                metadata=repository
            )
        )

        # Developer profiles
        for developer in repository_data.get("developers", []):
            records.append(
                self._create_record(
                    project_id=project_id,
                    source_name="Synthetic Developer",
                    source_id=developer["developer_id"],
                    title=developer["name"],
                    content=self._developer_content(developer),
                    author=developer["name"],
                    created_at=developer.get("joined_at"),
                    updated_at=developer.get("left_at"),
                    metadata=developer
                )
            )

        # Commits
        for commit in repository_data.get("commits", []):
            records.append(
                self._create_record(
                    project_id=project_id,
                    source_name="Synthetic Commit",
                    source_id=commit["commit_id"],
                    title=commit["title"],
                    content=commit["message"],
                    author=commit["author"],
                    created_at=commit["date"],
                    metadata=commit
                )
            )

        # Issues
        for issue in repository_data.get("issues", []):
            records.append(
                self._create_record(
                    project_id=project_id,
                    source_name="Synthetic Issue",
                    source_id=issue["issue_id"],
                    title=issue["title"],
                    content=issue["description"],
                    author=issue["reported_by"],
                    created_at=issue["created_at"],
                    updated_at=issue["updated_at"],
                    metadata=issue
                )
            )

        # Pull requests
        for pull_request in repository_data.get("pull_requests", []):
            records.append(
                self._create_record(
                    project_id=project_id,
                    source_name="Synthetic Pull Request",
                    source_id=pull_request["pull_request_id"],
                    title=pull_request["title"],
                    content=self._pull_request_content(pull_request),
                    author=pull_request["author"],
                    created_at=pull_request["created_at"],
                    updated_at=pull_request["merged_at"],
                    metadata=pull_request
                )
            )

        # Technical discussions
        for discussion in repository_data.get("discussions", []):
            records.append(
                self._create_record(
                    project_id=project_id,
                    source_name="Synthetic Discussion",
                    source_id=discussion["discussion_id"],
                    title=discussion["title"],
                    content=discussion["content"],
                    author=discussion["author"],
                    created_at=discussion["created_at"],
                    metadata=discussion
                )
            )

        # Project events
        for event in repository_data.get("events", []):
            records.append(
                self._create_record(
                    project_id=project_id,
                    source_name="Synthetic Project Event",
                    source_id=event["event_id"],
                    title=event["title"],
                    content=event["description"],
                    author=event["developer"],
                    created_at=event["created_at"],
                    metadata=event
                )
            )

        # Technical dependencies
        for dependency in repository_data.get("dependencies", []):
            records.append(
                self._create_record(
                    project_id=project_id,
                    source_name="Synthetic Dependency",
                    source_id=dependency["dependency_id"],
                    title=(
                        f'{dependency["source_module"]} '
                        f'-> {dependency["target_module"]}'
                    ),
                    content=dependency["description"],
                    author=dependency["responsible_developer"],
                    metadata=dependency
                )
            )

        return records

    def _create_record(
        self,
        project_id: str,
        source_name: str,
        source_id: str,
        title: str,
        content: str,
        author: str | None = None,
        created_at=None,
        updated_at=None,
        metadata: dict | None = None
    ) -> SourceRecord:
        """Create a validated standardized source record."""

        return SourceRecord(
            project_id=project_id,
            source_type=self.source_type,
            source_name=source_name,
            source_id=str(source_id),
            title=title,
            content=content or "",
            author=author,
            created_at=created_at,
            updated_at=updated_at,
            metadata=metadata or {}
        )

    @staticmethod
    def _developer_content(developer: dict) -> str:
        """Convert developer responsibilities into readable text."""

        responsibilities = ", ".join(
            developer.get("responsibilities", [])
        )

        return (
            f'Role: {developer.get("role", "Unknown")}\n'
            f'Responsibilities: {responsibilities}\n'
            f'Status: {developer.get("status", "Unknown")}\n'
            f'Departure reason: '
            f'{developer.get("departure_reason") or "Not applicable"}'
        )

    @staticmethod
    def _pull_request_content(pull_request: dict) -> str:
        """Combine PR description and review information."""

        return (
            f'Description: {pull_request.get("description", "")}\n'
            f'Review status: {pull_request.get("review_status", "Unknown")}\n'
            f'Reviewer: {pull_request.get("reviewer", "Unknown")}\n'
            f'Review comment: {pull_request.get("review_comment", "")}\n'
            f'Linked issue: {pull_request.get("linked_issue_id") or "None"}\n'
            f'Merged: {pull_request.get("merged", False)}'
        )