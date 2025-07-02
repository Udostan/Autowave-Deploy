/**
 * Professional History System for AutoWave
 * 
 * Features:
 * - Clean, professional UI
 * - Activity continuation support
 * - Real-time filtering and search
 * - Cross-agent compatibility
 * - Session restoration
 */

class ProfessionalHistorySystem {
    constructor() {
        this.isOpen = false;
        this.currentFilter = 'all';
        this.searchQuery = '';
        this.historyData = [];
        this.lastRefresh = 0;
        this.refreshInterval = null;

        this.init();
    }
    
    init() {
        console.log('Professional History System initializing...');
        this.bindEvents();
        this.setupVisibility();
        this.setupAutoRefresh();

        // Force immediate load
        this.forceLoadHistory();

        // Also load after a delay
        setTimeout(() => {
            console.log('Delayed history load starting...');
            this.forceLoadHistory();
        }, 2000);

        console.log('Professional History System initialized');
    }

    async forceLoadHistory() {
        console.log('Force loading history...');
        try {
            const response = await fetch('/api/history/unified?limit=50');
            console.log('Force load response status:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log('Force load data:', data);

            if (data.success && data.history && data.history.length > 0) {
                console.log(`Force load: ${data.history.length} items found`);
                this.historyData = data.history;
                this.forceRenderHistory();
            } else {
                console.log('Force load: No history data');
                this.forceShowEmpty();
            }
        } catch (error) {
            console.error('Force load error:', error);
        }
    }

    forceRenderHistory() {
        const listEl = document.getElementById('history-list');
        if (!listEl) {
            console.error('Force render: history-list not found');
            return;
        }

        console.log('Force rendering history items...');

        // Clear existing content
        listEl.innerHTML = '';

        // Add each history item using the proper createHistoryItem method
        this.historyData.forEach((item, index) => {
            console.log(`Force rendering item ${index + 1}:`, item.agent_display_name);
            const historyItem = this.createEnhancedHistoryItem(item);
            listEl.appendChild(historyItem);
        });

        console.log('Force render completed');

        // Hide empty state
        const emptyEl = document.getElementById('history-empty');
        if (emptyEl) emptyEl.style.display = 'none';

        // Hide loading state
        const loadingEl = document.getElementById('history-loading');
        if (loadingEl) loadingEl.style.display = 'none';
    }

    createEnhancedHistoryItem(item) {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.dataset.sessionId = item.session_id;
        div.dataset.agentType = item.agent_type;

        // Enhanced styling similar to Genspark/ChatGPT
        div.style.cssText = `
            padding: 12px;
            border: 1px solid #333;
            margin: 8px 0;
            background: #1a1a1a;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
        `;

        // Add hover effect
        div.addEventListener('mouseenter', () => {
            div.style.background = '#252525';
            div.style.borderColor = '#4CAF50';
        });

        div.addEventListener('mouseleave', () => {
            div.style.background = '#1a1a1a';
            div.style.borderColor = '#333';
        });

        const timeAgo = this.getTimeAgo(item.updated_at || item.created_at);

        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #4CAF50; font-weight: bold; font-size: 14px;">${item.agent_display_name}</span>
                <span style="color: #888; font-size: 11px;">${timeAgo}</span>
            </div>
            <div style="color: #ccc; margin-bottom: 8px; font-size: 13px; line-height: 1.4;">${item.preview_text}</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #666; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">${item.activity_type}</span>
                <div style="color: #4CAF50; font-size: 11px; display: flex; align-items: center; gap: 4px;">
                    <span>Continue</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M8.59 16.59L13.17 12L8.59 7.41L10 6l6 6-6 6-1.41-1.41z"/>
                    </svg>
                </div>
            </div>
        `;

        // Enhanced click handler with loading state and data restoration
        div.addEventListener('click', async (e) => {
            e.preventDefault();
            await this.continueActivityWithDataLoad(item, div);
        });

        return div;
    }

    forceShowEmpty() {
        const emptyEl = document.getElementById('history-empty');
        const loadingEl = document.getElementById('history-loading');

        if (emptyEl) emptyEl.style.display = 'block';
        if (loadingEl) loadingEl.style.display = 'none';

        console.log('Force showing empty state');
    }
    
    bindEvents() {
        const toggle = document.getElementById('history-toggle');
        const sidebar = document.getElementById('history-sidebar');
        const overlay = document.getElementById('history-overlay');
        const closeBtn = document.getElementById('close-history-sidebar');
        const refreshBtn = document.getElementById('refresh-history');
        const searchInput = document.getElementById('history-search');
        const filterChips = document.querySelectorAll('.filter-chip');

        console.log('History elements check:', {
            toggle: !!toggle,
            sidebar: !!sidebar,
            overlay: !!overlay,
            closeBtn: !!closeBtn,
            refreshBtn: !!refreshBtn
        });

        if (!toggle || !sidebar || !overlay || !closeBtn) {
            console.error('Missing history elements:', {
                toggle: !!toggle,
                sidebar: !!sidebar,
                overlay: !!overlay,
                closeBtn: !!closeBtn
            });
            return;
        }
        
        // Toggle sidebar
        toggle.addEventListener('click', (e) => {
            e.preventDefault();
            this.openSidebar();
        });
        
        // Close sidebar
        closeBtn.addEventListener('click', () => this.closeSidebar());
        overlay.addEventListener('click', () => this.closeSidebar());

        // Refresh history
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.manualRefresh());
        }
        
        // Search functionality
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchQuery = e.target.value.toLowerCase();
                this.filterHistory();
            });
        }
        
        // Filter functionality
        filterChips.forEach(chip => {
            chip.addEventListener('click', () => {
                // Update active filter
                filterChips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                
                this.currentFilter = chip.dataset.filter;
                this.filterHistory();
            });
        });
        
        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeSidebar();
            }
        });
    }
    
    setupVisibility() {
        const toggle = document.getElementById('history-toggle');
        const currentPath = window.location.pathname;

        if (toggle) {
            // Show on all pages except history page
            if (currentPath === '/history' || currentPath === '/new-history') {
                toggle.style.display = 'none';
            } else {
                toggle.style.display = 'block';
            }
        }
    }

    setupAutoRefresh() {
        // Auto-refresh history every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.refreshHistoryIfNeeded();
        }, 30000);

        // Refresh when page becomes visible (tab switching)
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.refreshHistoryIfNeeded();
            }
        });

        // Refresh when window gains focus
        window.addEventListener('focus', () => {
            this.refreshHistoryIfNeeded();
        });

        // Initial load immediately
        setTimeout(() => {
            console.log('Initial history load starting...');
            this.loadHistoryData();
        }, 1000);
    }

    async refreshHistoryIfNeeded() {
        const now = Date.now();
        const timeSinceLastRefresh = now - this.lastRefresh;

        // Only refresh if it's been more than 10 seconds since last refresh
        if (timeSinceLastRefresh > 10000) {
            console.log('Auto-refreshing history data...');
            await this.loadHistoryData();
        }
    }

    async manualRefresh() {
        const refreshBtn = document.getElementById('refresh-history');

        if (refreshBtn) {
            refreshBtn.classList.add('spinning');
        }

        console.log('Manual refresh triggered');
        await this.loadHistoryData();

        if (refreshBtn) {
            setTimeout(() => {
                refreshBtn.classList.remove('spinning');
            }, 500);
        }
    }
    
    async openSidebar() {
        const sidebar = document.getElementById('history-sidebar');
        const overlay = document.getElementById('history-overlay');

        if (!sidebar || !overlay) return;

        this.isOpen = true;
        sidebar.classList.add('open');
        overlay.classList.add('active');

        // Show cached data immediately if available
        if (this.historyData && this.historyData.length > 0) {
            console.log('Showing cached history data:', this.historyData.length, 'items');
            this.renderHistory(this.historyData);
        } else {
            console.log('No cached data, loading fresh data...');
            // Load fresh data if no cache
            await this.loadHistoryData();
        }
    }
    
    closeSidebar() {
        const sidebar = document.getElementById('history-sidebar');
        const overlay = document.getElementById('history-overlay');
        
        if (!sidebar || !overlay) return;
        
        this.isOpen = false;
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    }
    
    async loadHistoryData() {
        const loadingEl = document.getElementById('history-loading');
        const emptyEl = document.getElementById('history-empty');
        const listEl = document.getElementById('history-list');

        console.log('Loading history data, elements found:', {
            loadingEl: !!loadingEl,
            emptyEl: !!emptyEl,
            listEl: !!listEl
        });

        if (!listEl) {
            console.error('History list element not found, skipping history load');
            return;
        }

        try {
            // Show loading state only if sidebar is open
            if (this.isOpen && loadingEl) loadingEl.style.display = 'block';
            if (this.isOpen && emptyEl) emptyEl.style.display = 'none';

            console.log('Fetching history from API...');
            const response = await fetch('/api/history/unified?limit=50');
            console.log('API response status:', response.status);

            const data = await response.json();
            console.log('API response data:', data);

            if (data.success && data.history) {
                this.historyData = data.history;
                this.lastRefresh = Date.now();

                console.log(`History data loaded: ${this.historyData.length} items`);
                console.log('History items:', this.historyData);

                // Always render if we have data, regardless of sidebar state
                this.renderHistory(this.historyData);

                console.log(`History refreshed: ${this.historyData.length} items loaded`);
            } else {
                console.log('No history data or API error:', data);
                this.showEmptyState();
            }

        } catch (error) {
            console.error('Error loading history:', error);
            if (this.isOpen) {
                this.showEmptyState();
            }
        } finally {
            if (this.isOpen && loadingEl) loadingEl.style.display = 'none';
        }
    }
    
    renderHistory(historyItems) {
        const listEl = document.getElementById('history-list');
        const emptyEl = document.getElementById('history-empty');
        const loadingEl = document.getElementById('history-loading');

        console.log('Rendering history, listEl found:', !!listEl);
        console.log('History items to render:', historyItems ? historyItems.length : 0);

        if (!listEl) {
            console.error('History list element not found - cannot render history');
            return;
        }

        if (!historyItems || historyItems.length === 0) {
            console.log('No history items to render, showing empty state');
            this.showEmptyState();
            return;
        }

        // Hide loading and empty states
        if (loadingEl) loadingEl.style.display = 'none';
        if (emptyEl) emptyEl.style.display = 'none';

        // Clear existing items (except loading and empty states)
        const existingItems = listEl.querySelectorAll('.history-item');
        console.log('Clearing existing items:', existingItems.length);
        existingItems.forEach(item => item.remove());

        // Add new items
        historyItems.forEach((item, index) => {
            console.log(`Creating history item ${index + 1}:`, item.agent_display_name);
            const historyItem = this.createHistoryItem(item);
            listEl.appendChild(historyItem);
        });

        console.log('History rendering completed');
    }
    
    createHistoryItem(item) {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.dataset.sessionId = item.session_id;
        div.dataset.agentType = item.agent_type;
        
        const timeAgo = this.getTimeAgo(item.updated_at || item.created_at);
        
        div.innerHTML = `
            <div class="history-item-header">
                <div class="agent-badge">${item.agent_display_name || item.agent_type}</div>
                <div class="history-timestamp">${timeAgo}</div>
            </div>
            <div class="history-preview">${item.preview_text || 'No preview available'}</div>
            <div class="continue-indicator">
                <i class="fas fa-arrow-right"></i> Continue
            </div>
        `;
        
        // Add click handler for continuation
        div.addEventListener('click', () => {
            this.continueActivity(item);
        });
        
        return div;
    }
    
    async continueActivity(item) {
        try {
            console.log('Continuing activity:', item);

            // Close sidebar first
            this.closeSidebar();

            // Navigate to continuation URL
            if (item.continuation_url) {
                window.location.href = item.continuation_url;
            } else {
                // Fallback: redirect to agent page
                const agentUrls = {
                    'autowave_chat': '/autowave-chat',
                    'prime_agent': '/prime-agent-tools',
                    'agentic_code': '/agentic-code',
                    'research_lab': '/research-lab',
                    'agent_wave': '/document-generator'
                };

                const url = agentUrls[item.agent_type] || '/';
                window.location.href = url;
            }

        } catch (error) {
            console.error('Error continuing activity:', error);
        }
    }

    async continueActivityWithDataLoad(item, element) {
        try {
            console.log('Continuing activity with data load:', item);

            // Show loading state on the clicked item
            const originalContent = element.innerHTML;
            element.style.opacity = '0.7';
            element.style.pointerEvents = 'none';

            // Add loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #4CAF50;
                font-size: 12px;
                display: flex;
                align-items: center;
                gap: 8px;
            `;
            loadingDiv.innerHTML = `
                <div style="width: 16px; height: 16px; border: 2px solid #333; border-top: 2px solid #4CAF50; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                Loading...
            `;

            // Add CSS animation for spinner
            if (!document.getElementById('spinner-style')) {
                const style = document.createElement('style');
                style.id = 'spinner-style';
                style.textContent = `
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                `;
                document.head.appendChild(style);
            }

            element.appendChild(loadingDiv);

            // Fetch continuation data from the API
            let continuationData = null;
            try {
                console.log('Fetching continuation data for session:', item.session_id);
                const response = await fetch(`/api/history/continue/${item.session_id}`);

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        continuationData = data.continuation_data;
                        console.log('Continuation data loaded:', continuationData);
                    }
                }
            } catch (error) {
                console.warn('Could not load continuation data:', error);
            }

            // Store continuation data in localStorage for the target page to use
            if (continuationData) {
                localStorage.setItem('history_continuation_data', JSON.stringify({
                    sessionId: item.session_id,
                    agentType: item.agent_type,
                    data: continuationData,
                    timestamp: Date.now()
                }));
                console.log('Continuation data stored in localStorage');
            }

            // Store basic session info for restoration
            localStorage.setItem('restore_session_data', JSON.stringify({
                sessionId: item.session_id,
                agentType: item.agent_type,
                agentDisplayName: item.agent_display_name,
                activityType: item.activity_type,
                previewText: item.preview_text,
                timestamp: Date.now()
            }));

            // Close sidebar
            this.closeSidebar();

            // Small delay to show loading state
            await new Promise(resolve => setTimeout(resolve, 500));

            // Navigate to continuation URL
            if (item.continuation_url) {
                console.log('Navigating to:', item.continuation_url);
                window.location.href = item.continuation_url;
            } else {
                // Fallback: redirect to agent page with session ID
                const agentUrls = {
                    'autowave_chat': '/dark-chat',
                    'prime_agent': '/autowave',
                    'agentic_code': '/agentic-code',
                    'research_lab': '/research-lab',
                    'agent_wave': '/agent-wave',
                    'context7_tools': '/context7-tools'
                };

                const baseUrl = agentUrls[item.agent_type] || '/';
                const url = `${baseUrl}?session_id=${item.session_id}`;
                console.log('Navigating to fallback URL:', url);
                window.location.href = url;
            }

        } catch (error) {
            console.error('Error continuing activity with data load:', error);

            // Restore element state on error
            element.style.opacity = '1';
            element.style.pointerEvents = 'auto';
            element.innerHTML = originalContent;

            // Show error message
            alert('Failed to continue activity. Please try again.');
        }
    }
    
    filterHistory() {
        let filteredData = this.historyData;
        
        // Apply agent type filter
        if (this.currentFilter !== 'all') {
            filteredData = filteredData.filter(item => 
                item.agent_type === this.currentFilter
            );
        }
        
        // Apply search filter
        if (this.searchQuery) {
            filteredData = filteredData.filter(item => {
                const searchText = [
                    item.session_name || '',
                    item.preview_text || '',
                    item.agent_display_name || '',
                    item.agent_type || ''
                ].join(' ').toLowerCase();
                
                return searchText.includes(this.searchQuery);
            });
        }
        
        this.renderHistory(filteredData);
    }
    
    showEmptyState() {
        const emptyEl = document.getElementById('history-empty');
        if (emptyEl) {
            emptyEl.style.display = 'block';
        }
    }
    
    getTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString();
    }

    // Cleanup method
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // Static utility methods for session restoration
    static getStoredContinuationData() {
        try {
            const data = localStorage.getItem('history_continuation_data');
            if (data) {
                const parsed = JSON.parse(data);
                // Check if data is not too old (max 5 minutes)
                if (Date.now() - parsed.timestamp < 300000) {
                    return parsed;
                }
                // Clean up old data
                localStorage.removeItem('history_continuation_data');
            }
        } catch (error) {
            console.error('Error getting stored continuation data:', error);
        }
        return null;
    }

    static getStoredSessionData() {
        try {
            const data = localStorage.getItem('restore_session_data');
            if (data) {
                const parsed = JSON.parse(data);
                // Check if data is not too old (max 5 minutes)
                if (Date.now() - parsed.timestamp < 300000) {
                    return parsed;
                }
                // Clean up old data
                localStorage.removeItem('restore_session_data');
            }
        } catch (error) {
            console.error('Error getting stored session data:', error);
        }
        return null;
    }

    static clearStoredData() {
        try {
            localStorage.removeItem('history_continuation_data');
            localStorage.removeItem('restore_session_data');
            console.log('Cleared stored continuation data');
        } catch (error) {
            console.error('Error clearing stored data:', error);
        }
    }

    // Helper method to format timestamp
    formatTimestamp(dateString) {
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMins / 60);
            const diffDays = Math.floor(diffHours / 24);

            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffHours < 24) return `${diffHours}h ago`;
            if (diffDays < 7) return `${diffDays}d ago`;

            return date.toLocaleDateString();
        } catch (error) {
            return 'Unknown';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.professionalHistory = new ProfessionalHistorySystem();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProfessionalHistorySystem;
}
