/**
 * Workspace Page — "/workspace/[projectId]"
 */
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { WorkspaceShell } from "@/components/workspace/WorkspaceShell";

export const metadata = { title: "Workspace" };

interface WorkspacePageProps {
  params: Promise<{ projectId: string }>;
}

export default async function WorkspacePage({ params }: WorkspacePageProps) {
  const { projectId } = await params;
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/auth/login");

  return <WorkspaceShell projectId={projectId} />;
}