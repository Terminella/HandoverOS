import type { Project } from "./types";

export const PROJECT_STORAGE_KEY = "handoveros-selected-project";
export const PROJECT_CHANGE_EVENT = "handoveros-project-change";

export function deduplicateProjects<T extends { id: string }>(projects: T[]): T[] {
  const seen = new Set<string>();
  return projects.filter((project) => {
    if (seen.has(project.id)) return false;
    seen.add(project.id);
    return true;
  });
}

export function publishProjectSelection(projectId: string): void {
  localStorage.setItem(PROJECT_STORAGE_KEY, projectId);
  window.dispatchEvent(
    new CustomEvent(PROJECT_CHANGE_EVENT, {
      detail: { projectId },
    })
  );
}

export function isKnownProject(projects: Project[], projectId: string | null): projectId is string {
  return Boolean(projectId && projects.some((project) => project.id === projectId));
}
