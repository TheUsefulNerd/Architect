/**
 * useProjects Hook
 * Fetches and manages the list of user projects.
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import { projectsApi } from "@/lib/api";
import type { ProjectResponse, ProjectCreateRequest } from "@/types";

export function useProjects() {
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await projectsApi.list();
      setProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const createProject = async (data: ProjectCreateRequest) => {
    const project = await projectsApi.create(data);
    setProjects((prev) => [project, ...prev]);
    return project;
  };

  const deleteProject = async (id: string) => {
    await projectsApi.delete(id);
    setProjects((prev) => prev.filter((p) => p.id !== id));
  };

  return {
    projects,
    loading,
    error,
    refetch: fetchProjects,
    createProject,
    deleteProject,
  };
}