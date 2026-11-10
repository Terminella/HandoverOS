from datetime import datetime, timezone


class RepositoryGenerator:
    """
    Generates realistic synthetic repository data for HandoverOS.

    All developers, repositories and project activities are fictional.
    No external GitHub connection or authentication is required.
    """

    def __init__(self):
        self.repository = self._generate_repository()
        self.developers = self._generate_developers()

    def _generate_repository(self):
        """Generate fictional repository metadata."""

        return {
            "repository_id": "TASKFLOW-001",

            # Synthetic dataset identification
            "is_synthetic": True,
            "dataset_type": "demonstration",
            "dataset_name": "TaskFlow",
            "data_origin": "HandoverOS Synthetic Data Generator",


            "name": "TaskFlow",
            "full_name": "TaskFlow/TaskFlow",
            "description": (
                "An intelligent project management platform "
                "for teams to manage tasks, collaborate and "
                "track project progress."
            ),
            "visibility": "private",
            "language": "Python",
            "frameworks": [
                "FastAPI",
                "React",
                "PostgreSQL",
                "Redis"
            ],
            "created_at": datetime(
                2025, 1, 10, tzinfo=timezone.utc
            ),
            "default_branch": "main",
            "project_status": "active",
            "total_developers": 5,
            "modules": [
                "Authentication",
                "User Management",
                "Task Management",
                "Project Dashboard",
                "Notifications",
                "Database",
                "API Gateway",
                "Deployment"
            ]
        }

    def _generate_developers(self):
        """Generate fictional project developer profiles."""

        return [
            {
                "developer_id": "DEV001",
                "name": "Alex Morgan",
                "username": "alex_morgan",
                "role": "Backend Lead",
                "responsibilities": [
                    "Backend architecture",
                    "Authentication",
                    "API development",
                    "Code reviews"
                ],
                "joined_at": datetime(
                    2025, 1, 10, tzinfo=timezone.utc
                ),
                "left_at": datetime(
                    2025, 10, 13, tzinfo=timezone.utc
                ),
                "status": "departed",
                "departure_reason": "Voluntary departure"
            },
            {
                "developer_id": "DEV002",
                "name": "Sarah Chen",
                "username": "sarah_chen",
                "role": "Frontend Developer",
                "responsibilities": [
                    "Frontend architecture",
                    "Dashboard development",
                    "User interface",
                    "API integration"
                ],
                "joined_at": datetime(
                    2025, 1, 15, tzinfo=timezone.utc
                ),
                "left_at": None,
                "status": "active",
                "departure_reason": None
            },
            {
                "developer_id": "DEV003",
                "name": "Daniel Brooks",
                "username": "daniel_brooks",
                "role": "Database Engineer",
                "responsibilities": [
                    "Database architecture",
                    "Schema migrations",
                    "Query optimization",
                    "Data integrity"
                ],
                "joined_at": datetime(
                    2025, 1, 20, tzinfo=timezone.utc
                ),
                "left_at": None,
                "status": "active",
                "departure_reason": None
            },
            {
                "developer_id": "DEV004",
                "name": "Priya Sharma",
                "username": "priya_sharma",
                "role": "Full-Stack Developer",
                "responsibilities": [
                    "Notification system",
                    "Third-party integrations",
                    "Backend development",
                    "Bug fixing"
                ],
                "joined_at": datetime(
                    2025, 2, 1, tzinfo=timezone.utc
                ),
                "left_at": None,
                "status": "active",
                "departure_reason": None
            },
            {
                "developer_id": "DEV005",
                "name": "Ethan Cole",
                "username": "ethan_cole",
                "role": "DevOps Engineer",
                "responsibilities": [
                    "CI/CD pipelines",
                    "Deployment",
                    "Infrastructure",
                    "Monitoring"
                ],
                "joined_at": datetime(
                    2025, 2, 10, tzinfo=timezone.utc
                ),
                "left_at": None,
                "status": "active",
                "departure_reason": None
            }
        ]
    def _generate_commits(self):
        """Generate a realistic, chronological commit history."""

        commits = [
            ("2025-01-12", "DEV001", "Initial FastAPI project structure", "Created backend foundation and API configuration."),
            ("2025-01-15", "DEV001", "Implement user authentication", "Added initial email and password authentication."),
            ("2025-01-17", "DEV003", "Create initial database schema", "Added users, projects and tasks tables."),
            ("2025-01-20", "DEV002", "Build login interface", "Created login and registration pages."),
            ("2025-01-23", "DEV001", "Add JWT authentication middleware", "Implemented access token validation."),
            ("2025-01-25", "DEV002", "Integrate frontend login API", "Connected login interface with backend authentication."),
            ("2025-01-28", "DEV003", "Add refresh token database table", "Created persistent refresh token storage."),
            ("2025-02-03", "DEV004", "Implement notification service", "Added basic email notification functionality."),
            ("2025-02-07", "DEV005", "Configure Docker environment", "Created initial Docker configuration."),
            ("2025-02-12", "DEV001", "Implement role-based access control", "Added administrator and standard user permissions."),
            ("2025-02-16", "DEV002", "Build project dashboard", "Created dashboard layout and project overview."),
            ("2025-02-20", "DEV003", "Optimize task database queries", "Added indexes to frequently queried task fields."),
            ("2025-02-24", "DEV004", "Add task notification triggers", "Notifications now trigger when tasks are assigned."),
            ("2025-03-01", "DEV001", "Refactor authentication middleware", "Started redesigning token validation and refresh flow."),
            ("2025-03-04", "DEV002", "Add task creation interface", "Implemented task creation and editing forms."),
            ("2025-03-08", "DEV003", "Add project membership relationships", "Introduced project membership mapping."),
            ("2025-03-12", "DEV005", "Set up CI pipeline", "Added automated testing and build workflow."),
            ("2025-03-16", "DEV004", "Fix duplicate notification delivery", "Added basic duplicate notification prevention."),
            ("2025-03-20", "DEV001", "Introduce token rotation", "Added refresh token rotation but legacy sessions remain supported."),
            ("2025-03-24", "DEV002", "Implement task filtering", "Added filtering by status and assigned developer."),
            ("2025-04-02", "DEV003", "Redesign user database schema", "Changed user identifiers and membership relationships."),
            ("2025-04-06", "DEV001", "Update authentication user lookup", "Adjusted authentication queries for the new user schema."),
            ("2025-04-10", "DEV002", "Fix dashboard user mapping", "Updated frontend user mapping after schema changes."),
            ("2025-04-15", "DEV004", "Add notification retry mechanism", "Added retries for failed email deliveries."),
            ("2025-04-19", "DEV005", "Add production monitoring", "Integrated application health checks."),
            ("2025-05-01", "DEV001", "Begin authentication service migration", "Started separating authentication into an independent service."),
            ("2025-05-05", "DEV002", "Integrate new task API response", "Updated dashboard to consume the revised task response."),
            ("2025-05-10", "DEV003", "Add database migration tracking", "Introduced migration version tracking."),
            ("2025-05-15", "DEV004", "Implement in-app notifications", "Added notification storage and retrieval."),
            ("2025-05-20", "DEV005", "Configure staging deployment", "Created a separate staging environment."),
            ("2025-06-01", "DEV001", "Add authentication service endpoint", "New authentication endpoint is available but old endpoints remain."),
            ("2025-06-05", "DEV002", "Fix task dashboard pagination", "Resolved pagination errors for larger projects."),
            ("2025-06-10", "DEV003", "Optimize project membership queries", "Improved membership lookup performance."),
            ("2025-06-15", "DEV004", "Investigate notification delivery failures", "Identified intermittent failures during high traffic."),
            ("2025-06-20", "DEV005", "Add deployment rollback configuration", "Introduced rollback support for staging."),
            ("2025-07-01", "DEV001", "Add refresh token revocation endpoint", "Revocation endpoint is implemented but not yet integrated everywhere."),
            ("2025-07-06", "DEV002", "Implement project activity timeline", "Added recent activity to the project dashboard."),
            ("2025-07-11", "DEV003", "Add task archival support", "Archived tasks are now stored separately."),
            ("2025-07-16", "DEV004", "Fix notification retry race condition", "Partial fix applied; concurrent retries still need investigation."),
            ("2025-07-21", "DEV005", "Improve application logging", "Added structured logs for production debugging."),
            ("2025-08-01", "DEV001", "Refactor authentication token service", "Removed some legacy code; migration is still incomplete."),
            ("2025-08-06", "DEV002", "Add team management interface", "Created team member management screens."),
            ("2025-08-11", "DEV003", "Add database connection pooling", "Improved database connection handling."),
            ("2025-08-16", "DEV004", "Add notification preferences", "Users can configure notification preferences."),
            ("2025-08-21", "DEV005", "Configure production deployment", "Production deployment pipeline configured."),
            ("2025-09-01", "DEV001", "Document authentication migration plan", "Documented intended migration but some implementation details remain unresolved."),
            ("2025-09-05", "DEV002", "Fix dashboard permission handling", "Updated frontend permissions for team roles."),
            ("2025-09-10", "DEV003", "Add database backup verification", "Added backup integrity checks."),
            ("2025-09-15", "DEV004", "Investigate missing notification records", "Found that some failed deliveries are not recorded correctly."),
            ("2025-09-20", "DEV005", "Add production alerting", "Configured deployment and service alerts."),
            ("2025-09-25", "DEV001", "Begin final authentication migration", "Migration started but legacy compatibility remains unresolved."),
            ("2025-10-01", "DEV002", "Update frontend authentication handling", "Frontend still supports the legacy authentication response."),
            ("2025-10-04", "DEV003", "Add migration compatibility layer", "Temporary compatibility layer added for old user records."),
            ("2025-10-07", "DEV004", "Patch notification retry handling", "Improved retry handling without fully resolving duplicate delivery."),
            ("2025-10-09", "DEV005", "Verify production deployment", "Deployment verified with known authentication warnings."),
            ("2025-10-11", "DEV001", "WIP: authentication migration cleanup", "Work in progress. Legacy token handling and frontend compatibility are unfinished."),
            ("2025-10-12", "DEV001", "Add notes for authentication migration", "Recorded outstanding migration concerns in commit message."),
            ("2025-10-14", "DEV002", "Investigate login failures after migration", "Login failures reported after the backend changes."),
            ("2025-10-15", "DEV003", "Investigate user schema compatibility", "Old user records may not map correctly to the revised schema.")
        ]

        developer_lookup = {
            developer["developer_id"]: developer
            for developer in self.developers
        }

        generated_commits = []

        for index, (date, developer_id, title, message) in enumerate(commits, start=1):
            developer = developer_lookup[developer_id]

            generated_commits.append({
                "commit_id": f"TF-COMMIT-{index:03d}",
                "repository_id": self.repository["repository_id"],
                "developer_id": developer_id,
                "author": developer["name"],
                "date": datetime.fromisoformat(
                    f"{date}T10:00:00+00:00"
                ),
                "title": title,
                "message": message,
                "branch": "main",
                "status": "committed"
            })

        return generated_commits
    
    def _generate_issues(self):
        """Generate realistic synthetic project issues."""

        issues = [
            ("DEV002", "Login fails after authentication migration",
             "Users receive a 401 response when refreshing expired sessions.",
             "high", "open", ["authentication", "backend"]),

            ("DEV003", "Legacy user records fail schema validation",
             "Older user records do not contain the newly required membership fields.",
             "high", "open", ["database", "migration"]),

            ("DEV004", "Duplicate notifications during retry",
             "Users sometimes receive the same notification multiple times when delivery retries overlap.",
             "high", "open", ["notifications", "bug"]),

            ("DEV002", "Dashboard displays incorrect task ownership",
             "Tasks occasionally display the previous assignee after reassignment.",
             "medium", "open", ["frontend", "tasks"]),

            ("DEV005", "Production health check reports false failures",
             "The health endpoint occasionally times out during database connection spikes.",
             "medium", "open", ["deployment", "monitoring"]),

            ("DEV001", "Complete refresh token migration",
             "Legacy refresh tokens must be migrated or invalidated before removing old authentication endpoints.",
             "critical", "open", ["authentication", "security"]),

            ("DEV002", "Task pagination skips records",
             "Some tasks are missing when users navigate quickly between dashboard pages.",
             "medium", "closed", ["frontend", "tasks"]),

            ("DEV003", "Archived tasks appear in active task count",
             "Dashboard statistics include archived tasks in the active task total.",
             "low", "closed", ["database", "tasks"]),

            ("DEV004", "Failed email deliveries are not recorded",
             "Some failed notification attempts disappear without creating a delivery record.",
             "high", "open", ["notifications", "logging"]),

            ("DEV005", "Staging and production environment variables differ",
             "The production deployment uses an outdated notification configuration.",
             "medium", "closed", ["deployment", "configuration"]),

            ("DEV002", "Frontend uses outdated authentication response",
             "The frontend expects the legacy token response format instead of the new authentication service response.",
             "critical", "open", ["frontend", "authentication"]),

            ("DEV003", "Database migration rollback is incomplete",
             "Rolling back the membership schema migration does not restore all previous constraints.",
             "high", "open", ["database", "migration"]),

            ("DEV004", "Notification preferences are ignored for some events",
             "Task assignment notifications are sent even when users disable that notification category.",
             "medium", "open", ["notifications", "preferences"]),

            ("DEV005", "Deployment rollback leaves stale containers",
             "Old containers occasionally remain active after a failed deployment rollback.",
             "medium", "open", ["deployment", "infrastructure"]),

            ("DEV001", "Remove deprecated authentication endpoints",
             "Old authentication endpoints should be removed after frontend migration is complete.",
             "high", "open", ["authentication", "api"]),

            ("DEV002", "Project activity timeline has incorrect timestamps",
             "Some events display UTC timestamps without converting them to the user's selected timezone.",
             "low", "closed", ["frontend", "timeline"]),

            ("DEV003", "Database connection pool exhaustion",
             "Long-running requests can consume all available database connections.",
             "high", "open", ["database", "performance"]),

            ("DEV004", "Notification retry race condition remains",
             "The previous retry fix does not prevent duplicate delivery under concurrent requests.",
             "high", "open", ["notifications", "bug"]),

            ("DEV002", "Team permissions are inconsistent",
             "Users with viewer permissions can occasionally see editing controls.",
             "medium", "open", ["frontend", "permissions"]),

            ("DEV005", "Production deployment warnings are undocumented",
             "Authentication compatibility warnings appear during deployment but have no documented resolution.",
             "high", "open", ["deployment", "authentication"])
        ]

        issues_created = []

        for index, (
            developer_id,
            title,
            description,
            priority,
            state,
            labels
        ) in enumerate(issues, start=1):

            developer = next(
                dev for dev in self.developers
                if dev["developer_id"] == developer_id
            )

            issues_created.append({
                "issue_id": f"TF-ISSUE-{index:03d}",
                "issue_number": index,
                "repository_id": self.repository["repository_id"],
                "title": title,
                "description": description,
                "reported_by": developer["name"],
                "reporter_id": developer_id,
                "priority": priority,
                "state": state,
                "labels": labels,
                "created_at": datetime(
                    2025, 9, 1, 10, 0, tzinfo=timezone.utc
                ),
                "updated_at": datetime(
                    2025, 10, 15, 10, 0, tzinfo=timezone.utc
                ),
                "source": "synthetic"
            })
        return issues_created

    
    def _generate_pull_requests(self):
        """Generate realistic synthetic pull requests and reviews."""

        pull_requests = [
            {
                "author_id": "DEV001",
                "title": "Implement JWT authentication",
                "description": "Introduces JWT-based authentication with access and refresh tokens.",
                "state": "merged",
                "merged": True,
                "issue_id": None,
                "reviewer_id": "DEV003",
                "review_status": "approved",
                "review_comment": "Initial implementation looks good. Token expiry configuration should be documented.",
                "files_changed": ["auth/service.py", "auth/routes.py", "auth/middleware.py"],
                "created_at": "2025-01-22",
                "merged_at": "2025-01-25"
            },
            {
                "author_id": "DEV002",
                "title": "Add project dashboard",
                "description": "Introduces the main project dashboard and task overview.",
                "state": "merged",
                "merged": True,
                "issue_id": "TF-ISSUE-004",
                "reviewer_id": "DEV001",
                "review_status": "approved",
                "review_comment": "Dashboard structure is good. Task ownership mapping should be monitored.",
                "files_changed": ["frontend/dashboard.tsx", "frontend/project-card.tsx"],
                "created_at": "2025-02-14",
                "merged_at": "2025-02-17"
            },
            {
                "author_id": "DEV004",
                "title": "Add notification retry mechanism",
                "description": "Adds automatic retries when email notification delivery fails.",
                "state": "merged",
                "merged": True,
                "issue_id": "TF-ISSUE-009",
                "reviewer_id": "DEV003",
                "review_status": "approved",
                "review_comment": "Retry logic works, but concurrent retries may still produce duplicate notifications.",
                "files_changed": ["notifications/service.py", "notifications/retry.py"],
                "created_at": "2025-04-12",
                "merged_at": "2025-04-16"
            },
            {
                "author_id": "DEV003",
                "title": "Redesign user membership schema",
                "description": "Changes user identifiers and project membership relationships.",
                "state": "merged",
                "merged": True,
                "issue_id": "TF-ISSUE-002",
                "reviewer_id": "DEV001",
                "review_status": "approved",
                "review_comment": "Approved. Remember to maintain compatibility with older user records.",
                "files_changed": ["database/models/user.py", "database/models/membership.py", "database/migrations/"],
                "created_at": "2025-04-01",
                "merged_at": "2025-04-05"
            },
            {
                "author_id": "DEV001",
                "title": "Migrate authentication to new service",
                "description": "Moves authentication logic into a separate service. Legacy endpoint compatibility is not yet complete.",
                "state": "open",
                "merged": False,
                "issue_id": "TF-ISSUE-006",
                "reviewer_id": "DEV002",
                "review_status": "changes_requested",
                "review_comment": "The frontend still expects the legacy token response. Please provide a compatibility layer before this can be merged.",
                "files_changed": ["auth/service.py", "auth/routes.py", "auth/token_manager.py"],
                "created_at": "2025-09-24",
                "merged_at": None
            },
            {
                "author_id": "DEV002",
                "title": "Update frontend authentication integration",
                "description": "Updates the frontend to use the new authentication service response.",
                "state": "open",
                "merged": False,
                "issue_id": "TF-ISSUE-011",
                "reviewer_id": "DEV001",
                "review_status": "changes_requested",
                "review_comment": "Do not remove legacy response handling until the backend migration is verified in production.",
                "files_changed": ["frontend/auth/login.tsx", "frontend/auth/session.ts"],
                "created_at": "2025-10-01",
                "merged_at": None
            },
            {
                "author_id": "DEV003",
                "title": "Add legacy user compatibility layer",
                "description": "Adds temporary mapping for records created under the previous database schema.",
                "state": "open",
                "merged": False,
                "issue_id": "TF-ISSUE-012",
                "reviewer_id": "DEV001",
                "review_status": "pending",
                "review_comment": "Compatibility mapping needs testing against older production records.",
                "files_changed": ["database/compatibility/user_mapper.py", "database/migrations/"],
                "created_at": "2025-10-04",
                "merged_at": None
            },
            {
                "author_id": "DEV004",
                "title": "Fix notification retry race condition",
                "description": "Attempts to prevent duplicate notification delivery during concurrent retries.",
                "state": "open",
                "merged": False,
                "issue_id": "TF-ISSUE-018",
                "reviewer_id": "DEV003",
                "review_status": "changes_requested",
                "review_comment": "The locking mechanism does not cover all concurrent delivery paths. More testing is required.",
                "files_changed": ["notifications/retry.py", "notifications/worker.py"],
                "created_at": "2025-10-07",
                "merged_at": None
            },
            {
                "author_id": "DEV005",
                "title": "Improve production deployment rollback",
                "description": "Adds safer container cleanup and rollback handling.",
                "state": "merged",
                "merged": True,
                "issue_id": "TF-ISSUE-014",
                "reviewer_id": "DEV001",
                "review_status": "approved",
                "review_comment": "Rollback works in staging. Production monitoring should verify container cleanup.",
                "files_changed": ["deployment/rollback.py", "deployment/docker-compose.yml"],
                "created_at": "2025-06-18",
                "merged_at": "2025-06-22"
            },
            {
                "author_id": "DEV002",
                "title": "Implement team permissions interface",
                "description": "Adds frontend controls for administrator, editor and viewer permissions.",
                "state": "closed",
                "merged": False,
                "issue_id": "TF-ISSUE-019",
                "reviewer_id": "DEV001",
                "review_status": "changes_requested",
                "review_comment": "Frontend controls are not sufficient. The backend must enforce viewer restrictions too.",
                "files_changed": ["frontend/team/permissions.tsx"],
                "created_at": "2025-09-18",
                "merged_at": None
            },
            {
                "author_id": "DEV001",
                "title": "Remove legacy authentication endpoints",
                "description": "Attempts to remove deprecated authentication routes before the migration is fully verified.",
                "state": "closed",
                "merged": False,
                "issue_id": "TF-ISSUE-015",
                "reviewer_id": "DEV002",
                "review_status": "changes_requested",
                "review_comment": "Cannot remove these endpoints while the frontend and existing sessions still depend on them.",
                "files_changed": ["auth/routes.py", "auth/legacy.py"],
                "created_at": "2025-10-10",
                "merged_at": None
            },
            {
                "author_id": "DEV004",
                "title": "Record failed notification delivery attempts",
                "description": "Adds persistent records for unsuccessful email delivery attempts.",
                "state": "open",
                "merged": False,
                "issue_id": "TF-ISSUE-009",
                "reviewer_id": "DEV003",
                "review_status": "pending",
                "review_comment": "Please verify that retry attempts and final delivery status are stored separately.",
                "files_changed": ["notifications/service.py", "notifications/models.py"],
                "created_at": "2025-10-12",
                "merged_at": None
            }
        ]

        developer_lookup = {
            developer["developer_id"]: developer
            for developer in self.developers
        }

        generated_pull_requests = []

        for index, pr in enumerate(pull_requests, start=1):
            author = developer_lookup[pr["author_id"]]
            reviewer = developer_lookup[pr["reviewer_id"]]

            generated_pull_requests.append({
                "pull_request_id": f"TF-PR-{index:03d}",
                "pull_request_number": index,
                "repository_id": self.repository["repository_id"],
                "title": pr["title"],
                "description": pr["description"],
                "author_id": pr["author_id"],
                "author": author["name"],
                "reviewer_id": pr["reviewer_id"],
                "reviewer": reviewer["name"],
                "state": pr["state"],
                "merged": pr["merged"],
                "review_status": pr["review_status"],
                "review_comment": pr["review_comment"],
                "linked_issue_id": pr["issue_id"],
                "files_changed": pr["files_changed"],
                "created_at": datetime.fromisoformat(
                    f'{pr["created_at"]}T10:00:00+00:00'
                ),
                "merged_at": (
                    datetime.fromisoformat(
                        f'{pr["merged_at"]}T10:00:00+00:00'
                    )
                    if pr["merged_at"]
                    else None
                ),
                "source": "synthetic"
            })

        return generated_pull_requests

    def _generate_discussions(self):
        """Generate synthetic technical discussions and project decisions."""

        discussions = [
            ("DEV001", "2025-02-10", "Authentication architecture",
             "We should use JWT access tokens with refresh tokens. This will keep API authentication stateless while allowing session renewal.",
             "architecture", "Authentication", None),

            ("DEV003", "2025-02-11", "Refresh token storage",
             "Refresh tokens should be stored in the database so that we can revoke sessions when necessary.",
             "technical_decision", "Authentication", None),

            ("DEV002", "2025-02-12", "Frontend session handling",
             "The frontend will store the access token in memory and request a new one when the current token expires.",
             "implementation", "Authentication", None),

            ("DEV001", "2025-03-02", "Authentication middleware redesign",
             "The existing middleware has become difficult to maintain. I want to separate token validation from user lookup.",
             "architecture", "Authentication", None),

            ("DEV003", "2025-04-01", "User schema migration",
             "We need to change the user identifier structure before adding more complex team membership relationships.",
             "technical_decision", "Database", "TF-ISSUE-002"),

            ("DEV002", "2025-04-03", "Frontend compatibility warning",
             "Changing user identifiers will affect the dashboard because some components currently use the old user ID.",
             "risk", "User Management", "TF-ISSUE-002"),

            ("DEV001", "2025-04-04", "Schema migration compatibility",
             "Keep a compatibility mapping for existing users. We cannot assume every production record follows the new schema.",
             "technical_decision", "Database", "TF-ISSUE-002"),

            ("DEV004", "2025-04-16", "Notification retry design",
             "We should retry failed email notifications, but retries must not send the same notification twice.",
             "architecture", "Notifications", "TF-ISSUE-003"),

            ("DEV003", "2025-04-17", "Notification duplicate risk",
             "A simple retry loop is not enough. We need an idempotency mechanism to prevent duplicate deliveries.",
             "risk", "Notifications", "TF-ISSUE-003"),

            ("DEV005", "2025-05-18", "Staging environment",
             "All major backend changes should be tested in staging before production deployment.",
             "technical_decision", "Deployment", None),

            ("DEV001", "2025-05-25", "Authentication service separation",
             "I want to move authentication into a separate service so that other modules do not directly depend on its internal implementation.",
             "architecture", "Authentication", None),

            ("DEV002", "2025-06-02", "API response compatibility",
             "If the authentication response changes, the frontend needs advance notice. Otherwise login and session restoration may break.",
             "dependency", "Authentication", "TF-ISSUE-011"),

            ("DEV001", "2025-06-03", "Legacy endpoint decision",
             "We should keep the old authentication endpoints until the frontend migration is complete.",
             "technical_decision", "Authentication", None),

            ("DEV004", "2025-06-16", "Notification delivery failures",
             "Some notification failures are not appearing in our logs. We need to store failed delivery attempts separately.",
             "unresolved_question", "Notifications", "TF-ISSUE-009"),

            ("DEV003", "2025-06-17", "Database connection pool",
             "We should monitor connection usage before increasing the pool size. Increasing it blindly may overload the database.",
             "risk", "Database", "TF-ISSUE-017"),

            ("DEV005", "2025-07-03", "Deployment rollback strategy",
             "Rollback should restore the previous application version and remove containers created by the failed deployment.",
             "technical_decision", "Deployment", "TF-ISSUE-014"),

            ("DEV004", "2025-07-18", "Notification retry workaround",
             "Reducing concurrent retries seems to reduce duplicate messages, but this is only a temporary workaround.",
             "workaround", "Notifications", "TF-ISSUE-018"),

            ("DEV001", "2025-08-02", "Legacy authentication cleanup",
             "We can remove the legacy token implementation only after confirming that existing sessions have been migrated.",
             "dependency", "Authentication", "TF-ISSUE-015"),

            ("DEV002", "2025-08-04", "Frontend migration concern",
             "I cannot complete the frontend migration until the backend team confirms the final token response format.",
             "dependency", "Authentication", "TF-ISSUE-011"),

            ("DEV003", "2025-08-12", "Old user records",
             "Some older records do not contain the new membership fields. We need to decide whether to backfill them or support both formats.",
             "unresolved_question", "Database", "TF-ISSUE-012"),

            ("DEV001", "2025-09-01", "Authentication migration plan",
             "The migration will happen in stages: new service, frontend integration, session compatibility, then removal of legacy endpoints.",
             "technical_decision", "Authentication", "TF-ISSUE-006"),

            ("DEV002", "2025-09-26", "Frontend migration blocked",
             "The new authentication endpoint is available, but I still need a stable response contract before removing the old integration.",
             "blocker", "Authentication", "TF-ISSUE-011"),

            ("DEV003", "2025-10-05", "Compatibility layer concerns",
             "The compatibility layer handles most older records, but we have not tested all production data combinations.",
             "risk", "Database", "TF-ISSUE-012"),

            ("DEV004", "2025-10-08", "Notification race condition",
             "The recent retry patch reduces duplicate messages but does not guarantee exactly-once delivery.",
             "unresolved_question", "Notifications", "TF-ISSUE-018"),

            ("DEV001", "2025-10-11", "Authentication migration handover",
             "The migration is not complete. Legacy token handling still exists, frontend compatibility needs verification, and old endpoints must not be removed yet.",
             "handover_note", "Authentication", "TF-ISSUE-006"),

            ("DEV005", "2025-10-12", "Production deployment warning",
             "Production is running with authentication compatibility warnings. Do not assume the migration is safe just because deployment succeeded.",
             "risk", "Deployment", "TF-ISSUE-020"),

            ("DEV002", "2025-10-14", "Login failures after migration",
             "Login failures started appearing after the recent backend changes. We need Alex's migration notes to understand the intended token flow.",
             "unresolved_question", "Authentication", "TF-ISSUE-001")
        ]

        developer_lookup = {
            developer["developer_id"]: developer
            for developer in self.developers
        }

        generated_discussions = []

        for index, discussion in enumerate(discussions, start=1):
            (
                developer_id,
                date,
                title,
                content,
                category,
                module,
                linked_issue
            ) = discussion

            developer = developer_lookup[developer_id]

            generated_discussions.append({
                "discussion_id": f"TF-DISC-{index:03d}",
                "repository_id": self.repository["repository_id"],
                "author_id": developer_id,
                "author": developer["name"],
                "title": title,
                "content": content,
                "category": category,
                "module": module,
                "linked_issue_id": linked_issue,
                "created_at": datetime.fromisoformat(
                    f"{date}T12:00:00+00:00"
                ),
                "source": "synthetic"
            })

        return generated_discussions      

    def _generate_project_events(self):
        """Generate important synthetic project lifecycle events."""

        events = [
            ("2025-01-10", "project_created", "TaskFlow project initiated",
             "The TaskFlow project was officially started.", "DEV001"),

            ("2025-02-10", "team_expansion", "Development team expanded",
             "Priya Sharma and Ethan Cole joined the development team.", "DEV001"),

            ("2025-03-01", "architecture_change", "Authentication redesign initiated",
             "The team decided to separate authentication logic from the main backend.", "DEV001"),

            ("2025-04-02", "database_migration", "User schema redesigned",
             "The user identifier and membership database structure were changed.", "DEV003"),

            ("2025-05-01", "architecture_change", "Authentication service migration started",
             "Authentication began moving into an independent service.", "DEV001"),

            ("2025-06-15", "incident", "Notification delivery failures discovered",
             "Intermittent notification failures were discovered under high traffic.", "DEV004"),

            ("2025-07-16", "incident", "Notification retry race condition identified",
             "Concurrent retry operations were found to produce duplicate notifications.", "DEV004"),

            ("2025-09-25", "migration", "Final authentication migration started",
             "The team began the final authentication migration while legacy compatibility remained unresolved.", "DEV001"),

            ("2025-10-11", "work_in_progress", "Authentication migration left incomplete",
             "The final migration cleanup was unfinished when the backend lead prepared to leave.", "DEV001"),

            ("2025-10-13", "developer_departure", "Backend lead Alex Morgan departed",
             "Alex Morgan left the project. Authentication migration knowledge and ownership require handover.", "DEV001"),

            ("2025-10-14", "incident", "Login failures reported",
             "Frontend developers reported login failures following recent backend changes.", "DEV002"),

            ("2025-10-15", "risk", "Production compatibility risk identified",
             "Legacy user records and authentication compatibility remain unresolved.", "DEV003")
        ]

        events_created = []

        for index, event in enumerate(events, start=1):
            date, event_type, title, description, developer_id = event

            developer = next(
                dev for dev in self.developers
                if dev["developer_id"] == developer_id
            )

            events_created.append({
                "event_id": f"TF-EVENT-{index:03d}",
                "repository_id": self.repository["repository_id"],
                "event_type": event_type,
                "title": title,
                "description": description,
                "developer_id": developer_id,
                "developer": developer["name"],
                "created_at": datetime.fromisoformat(
                    f"{date}T10:00:00+00:00"
                ),
                "source": "synthetic"
            })

        return events_created

    def _generate_dependencies(self):
        """Generate technical dependencies between project modules."""

        return [
            {
                "dependency_id": "TF-DEP-001",
                "source_module": "Frontend Authentication",
                "target_module": "Authentication Service",
                "dependency_type": "API dependency",
                "description": "Frontend login and session restoration depend on the authentication API response format.",
                "status": "at_risk",
                "responsible_developer": "DEV001"
            },
            {
                "dependency_id": "TF-DEP-002",
                "source_module": "Authentication Service",
                "target_module": "User Database",
                "dependency_type": "Data dependency",
                "description": "Authentication user lookup depends on the redesigned user schema.",
                "status": "at_risk",
                "responsible_developer": "DEV003"
            },
            {
                "dependency_id": "TF-DEP-003",
                "source_module": "Notification Worker",
                "target_module": "Notification Database",
                "dependency_type": "Storage dependency",
                "description": "Notification retries require persistent delivery and retry records.",
                "status": "incomplete",
                "responsible_developer": "DEV004"
            },
            {
                "dependency_id": "TF-DEP-004",
                "source_module": "Project Dashboard",
                "target_module": "Task Management API",
                "dependency_type": "API dependency",
                "description": "Dashboard task ownership and pagination depend on the task API response.",
                "status": "active",
                "responsible_developer": "DEV002"
            },
            {
                "dependency_id": "TF-DEP-005",
                "source_module": "Deployment Pipeline",
                "target_module": "Environment Configuration",
                "dependency_type": "Configuration dependency",
                "description": "Production deployment requires consistent environment variables.",
                "status": "active",
                "responsible_developer": "DEV005"
            },
            {
                "dependency_id": "TF-DEP-006",
                "source_module": "Authentication Service",
                "target_module": "Legacy Authentication",
                "dependency_type": "Backward compatibility",
                "description": "Existing sessions still depend on legacy token handling.",
                "status": "at_risk",
                "responsible_developer": "DEV001"
            },
            {
                "dependency_id": "TF-DEP-007",
                "source_module": "Team Permissions UI",
                "target_module": "Backend Authorization",
                "dependency_type": "Security dependency",
                "description": "Frontend permission controls must match backend authorization rules.",
                "status": "incomplete",
                "responsible_developer": "DEV002"
            },
            {
                "dependency_id": "TF-DEP-008",
                "source_module": "Production Monitoring",
                "target_module": "Application Health API",
                "dependency_type": "Monitoring dependency",
                "description": "Production monitoring depends on reliable application health responses.",
                "status": "at_risk",
                "responsible_developer": "DEV005"
            }
        ]


    def generate_base_data(self):
        """Generate the complete synthetic TaskFlow repository."""

        return {
            "repository": self.repository,
            "developers": self.developers,
            "commits": self._generate_commits(),
            "issues": self._generate_issues(),
            "pull_requests": self._generate_pull_requests(),
            "discussions": self._generate_discussions(),
            "events": self._generate_project_events(),
            "dependencies": self._generate_dependencies()
        }


if __name__ == "__main__":
    generator = RepositoryGenerator()
    data = generator.generate_base_data()

    print("Repository:", data["repository"]["name"])
    print("Developers:", len(data["developers"]))
    print("Commits:", len(data["commits"]))
    print("Issues:", len(data["issues"]))

    print("\nLatest 5 commits:")

    for commit in data["commits"][-5:]:
        print(
            f'{commit["date"].date()} | '
            f'{commit["author"]} | '
            f'{commit["title"]}'
        )

    print("\nLatest 5 issues:")

    for issue in data["issues"][-5:]:
        print(
            f'{issue["issue_id"]} | '
            f'{issue["priority"].upper()} | '
            f'{issue["state"]} | '
            f'{issue["title"]}'
        )

    print("Pull Requests:", len(data["pull_requests"]))

    print("\nAll Pull Requests:")

    for pr in data["pull_requests"]:
        print(
            f'{pr["pull_request_id"]} | '
            f'{pr["state"].upper()} | '
            f'{pr["review_status"]} | '
            f'{pr["title"]}'
        )

    print("Discussions:", len(data["discussions"]))

    print("\nLatest 5 discussions:")

    for discussion in data["discussions"][-5:]:
        print(
            f'{discussion["discussion_id"]} | '
            f'{discussion["author"]} | '
            f'{discussion["category"]} | '
            f'{discussion["title"]}'
        )

    print("Project Events:", len(data["events"]))
    print("Dependencies:", len(data["dependencies"]))
