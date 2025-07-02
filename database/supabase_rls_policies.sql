-- AutoWave Supabase Row Level Security (RLS) Policies
-- Ensures users can only access their own data

-- 1. User Profiles Policies
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON public.user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- 2. Agent Sessions Policies
CREATE POLICY "Users can view own sessions" ON public.agent_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions" ON public.agent_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON public.agent_sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- 3. User Activities Policies
CREATE POLICY "Users can view own activities" ON public.user_activities
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own activities" ON public.user_activities
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own activities" ON public.user_activities
    FOR UPDATE USING (auth.uid() = user_id);

-- 4. File Uploads Policies
CREATE POLICY "Users can view own files" ON public.file_uploads
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own files" ON public.file_uploads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own files" ON public.file_uploads
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own files" ON public.file_uploads
    FOR DELETE USING (auth.uid() = user_id);

-- 5. Chat Conversations Policies
CREATE POLICY "Users can view own chats" ON public.chat_conversations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own chats" ON public.chat_conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 6. Prime Agent Tasks Policies
CREATE POLICY "Users can view own tasks" ON public.prime_agent_tasks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own tasks" ON public.prime_agent_tasks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own tasks" ON public.prime_agent_tasks
    FOR UPDATE USING (auth.uid() = user_id);

-- 7. Code Projects Policies
CREATE POLICY "Users can view own projects" ON public.code_projects
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own projects" ON public.code_projects
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects" ON public.code_projects
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects" ON public.code_projects
    FOR DELETE USING (auth.uid() = user_id);

-- 8. Research Queries Policies
CREATE POLICY "Users can view own research" ON public.research_queries
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own research" ON public.research_queries
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own research" ON public.research_queries
    FOR UPDATE USING (auth.uid() = user_id);

-- 9. Context7 Usage Policies
CREATE POLICY "Users can view own context7 usage" ON public.context7_usage
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own context7 usage" ON public.context7_usage
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own context7 usage" ON public.context7_usage
    FOR UPDATE USING (auth.uid() = user_id);

-- 10. Agent Wave Campaigns Policies
CREATE POLICY "Users can view own campaigns" ON public.agent_wave_campaigns
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own campaigns" ON public.agent_wave_campaigns
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own campaigns" ON public.agent_wave_campaigns
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own campaigns" ON public.agent_wave_campaigns
    FOR DELETE USING (auth.uid() = user_id);

-- 11. Memory Links Policies
CREATE POLICY "Users can view own memory links" ON public.memory_links
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own memory links" ON public.memory_links
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 12. User Preferences Policies
CREATE POLICY "Users can view own preferences" ON public.user_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences" ON public.user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences" ON public.user_preferences
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own preferences" ON public.user_preferences
    FOR DELETE USING (auth.uid() = user_id);

-- 13. Usage Analytics Policies
CREATE POLICY "Users can view own analytics" ON public.usage_analytics
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own analytics" ON public.usage_analytics
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own analytics" ON public.usage_analytics
    FOR UPDATE USING (auth.uid() = user_id);

-- Functions for automatic user profile creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, full_name)
    VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to automatically create user profile when user signs up
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update user activity count
CREATE OR REPLACE FUNCTION public.update_user_activity_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.user_profiles 
    SET total_activities = total_activities + 1,
        updated_at = NOW()
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update activity count when new activity is created
CREATE TRIGGER on_activity_created
    AFTER INSERT ON public.user_activities
    FOR EACH ROW EXECUTE FUNCTION public.update_user_activity_count();

-- Function to update session interaction count
CREATE OR REPLACE FUNCTION public.update_session_interactions()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.agent_sessions 
    SET total_interactions = total_interactions + 1
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update session interactions
CREATE TRIGGER on_session_activity
    AFTER INSERT ON public.user_activities
    FOR EACH ROW 
    WHEN (NEW.session_id IS NOT NULL)
    EXECUTE FUNCTION public.update_session_interactions();
