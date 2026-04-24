-- Architect Database Schema for Supabase PostgreSQL
-- Run this in your Supabase SQL Editor

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- NOTE: No custom `users` table — Supabase Auth manages users in auth.users.
-- projects.user_id references auth.users(id) directly so auth.uid() works in RLS policies.

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions table (conversation sessions)
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
    current_phase VARCHAR(50) DEFAULT 'planner' CHECK (current_phase IN ('planner', 'librarian', 'mentor')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table (chat history)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    phase VARCHAR(50) CHECK (phase IN ('planner', 'librarian', 'mentor')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Technical Specs table (output from Planner phase)
CREATE TABLE IF NOT EXISTS technical_specs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE NOT NULL,
    requirements TEXT,
    architecture TEXT,
    tech_stack JSONB DEFAULT '{}',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Documentation Links (from Librarian phase)
CREATE TABLE IF NOT EXISTS documentation_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE NOT NULL,
    tech_name VARCHAR(255),
    doc_url TEXT NOT NULL,
    scraped_content TEXT,
    relevance_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Code Scaffolds (from Mentor phase)
CREATE TABLE IF NOT EXISTS code_scaffolds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE NOT NULL,
    file_path VARCHAR(500),
    content TEXT,
    hints JSONB DEFAULT '[]',
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── Indexes ──────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_project_id ON sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_technical_specs_session_id ON technical_specs(session_id);
CREATE INDEX IF NOT EXISTS idx_documentation_links_session_id ON documentation_links(session_id);
CREATE INDEX IF NOT EXISTS idx_code_scaffolds_session_id ON code_scaffolds(session_id);

-- ─── updated_at trigger ───────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ─── Enable RLS ───────────────────────────────────────────────────────────────

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE technical_specs ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentation_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_scaffolds ENABLE ROW LEVEL SECURITY;

-- ─── RLS Policies ─────────────────────────────────────────────────────────────
-- Backend uses service_role key which bypasses RLS automatically.
-- These policies protect against any direct anon/authenticated client access.

-- PROJECTS — scoped directly by user_id = auth.uid()
CREATE POLICY "users_select_own_projects" ON projects
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_projects" ON projects
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "users_update_own_projects" ON projects
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "users_delete_own_projects" ON projects
    FOR DELETE USING (auth.uid() = user_id);

-- SESSIONS — scoped via projects
CREATE POLICY "users_select_own_sessions" ON sessions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = sessions.project_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_insert_own_sessions" ON sessions
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = sessions.project_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_update_own_sessions" ON sessions
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = sessions.project_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_delete_own_sessions" ON sessions
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = sessions.project_id
              AND projects.user_id = auth.uid()
        )
    );

-- MESSAGES — scoped via sessions → projects
CREATE POLICY "users_select_own_messages" ON messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = messages.session_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_insert_own_messages" ON messages
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = messages.session_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_delete_own_messages" ON messages
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = messages.session_id
              AND projects.user_id = auth.uid()
        )
    );

-- TECHNICAL SPECS — scoped via sessions → projects
CREATE POLICY "users_select_own_specs" ON technical_specs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = technical_specs.session_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_insert_own_specs" ON technical_specs
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = technical_specs.session_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_delete_own_specs" ON technical_specs
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = technical_specs.session_id
              AND projects.user_id = auth.uid()
        )
    );

-- DOCUMENTATION LINKS — scoped via sessions → projects
CREATE POLICY "users_select_own_docs" ON documentation_links
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = documentation_links.session_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_insert_own_docs" ON documentation_links
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = documentation_links.session_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_delete_own_docs" ON documentation_links
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = documentation_links.session_id
              AND projects.user_id = auth.uid()
        )
    );

-- CODE SCAFFOLDS — scoped via sessions → projects
CREATE POLICY "users_select_own_scaffolds" ON code_scaffolds
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = code_scaffolds.session_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_insert_own_scaffolds" ON code_scaffolds
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = code_scaffolds.session_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_update_own_scaffolds" ON code_scaffolds
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = code_scaffolds.session_id
              AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "users_delete_own_scaffolds" ON code_scaffolds
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM sessions
            JOIN projects ON projects.id = sessions.project_id
            WHERE sessions.id = code_scaffolds.session_id
              AND projects.user_id = auth.uid()
        )
    );

-- ─── Verification queries ─────────────────────────────────────────────────────
-- SELECT * FROM projects;
-- SELECT * FROM sessions;
-- SELECT * FROM messages;