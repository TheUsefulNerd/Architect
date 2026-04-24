/**
 * Dashboard Page — "/dashboard"
 * Lists user projects and allows creating new ones.
 */
import { redirect } from "next/navigation";
import Link from "next/link";
import {
  Layers,
  LogOut,
  User,
} from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import { CreateProjectDialog } from "@/components/dashboard/CreateProjectDialog";
import { ProjectsList } from "@/components/dashboard/ProjectsList";

export const metadata = { title: "Dashboard" };

export default async function DashboardPage() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/auth/login");

  return (
    <div className="flex min-h-screen flex-col bg-[#080c14]">

      {/* Topbar */}
      <header className="glass sticky top-0 z-50 border-b border-white/5 px-8 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">

          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 ring-1 ring-indigo-500/40">
              <Layers className="h-3.5 w-3.5 text-indigo-400" />
            </div>
            <span
              className="text-base text-slate-100"
              style={{ fontFamily: "var(--font-display)" }}
            >
              Architect
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-xl border border-white/8 bg-white/4 px-3 py-1.5">
              <User className="h-3.5 w-3.5 text-slate-500" />
              <span className="text-xs text-slate-400">{user.email}</span>
            </div>
            <form action="/auth/signout" method="post">
              <button className="flex items-center gap-1.5 rounded-xl border border-white/8 bg-white/4 px-3 py-1.5 text-xs text-slate-400 transition hover:bg-white/8 hover:text-slate-200">
                <LogOut className="h-3 w-3" />
                Sign out
              </button>
            </form>
          </div>

        </div>
      </header>

      {/* Main */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-8 py-12">
        <div className="mb-10 flex items-end justify-between">
          <div>
            <h1
              className="mb-1 text-3xl text-slate-50"
              style={{ fontFamily: "var(--font-display)" }}
            >
              Projects
            </h1>
          </div>
          <CreateProjectDialog trigger="icon" />
        </div>

        <ProjectsList />

      </main>
    </div>
  );
}