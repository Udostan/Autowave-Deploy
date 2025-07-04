/**
 * Universal Credit System for AutoWave Platform
 * Handles credit checking, consumption, and user feedback across all agent pages
 */

class UniversalCreditSystem {
    constructor() {
        this.userCredits = {
            remaining: 50,
            total: 50,
            plan: 'free',
            type: 'daily'
        };
        this.isInitialized = false;
        this.version = '2.0.1'; // Cache buster for admin fix
        this.creditCosts = {
            // Basic AI Tasks
            'chat_message': 1,
            'simple_search': 2,
            'text_generation': 2,
            'basic_query': 1,

            // AutoWave Chat (dark-chat)
            'autowave_chat_basic': 2,
            'autowave_chat_advanced': 4,

            // Prime Agent (autowave)
            'prime_agent_task': 5,
            'prime_agent_complex': 8,

            // Agent Wave (document-generator)
            'agent_wave_email': 8,
            'agent_wave_seo': 12,
            'agent_wave_learning': 15,
            'agent_wave_document': 10,

            // Research Lab (deep-research)
            'research_basic': 10,
            'research_advanced': 20,
            'research_comprehensive': 30,

            // Agentic Code (Design)
            'code_generation_simple': 15,
            'code_generation_advanced': 25,
            'code_generation_complex': 35,

            // Context7 Tools (Prime Agent Tools)
            'context7_restaurant_booking': 8,
            'context7_real_estate': 12,
            'context7_flight_search': 10,
            'context7_hotel_booking': 8,
            'context7_travel_planning': 15,
            'context7_job_search': 10,
            'context7_package_tracking': 8,
            'context7_weather_forecast': 5,
            'context7_news_research': 8,
            'context7_product_research': 10,
            'context7_price_comparison': 8,
            'context7_social_media': 6,
            'context7_email_assistant': 8,
            'context7_calendar_management': 6,
            'context7_task_management': 6,
            'context7_note_taking': 5,
            'context7_translation': 5,
            'context7_currency_converter': 3,
            'context7_unit_converter': 3,
            'context7_qr_generator': 3,
            'context7_password_generator': 2,
            'context7_color_palette': 4,
            'context7_image_optimizer': 6,
            'context7_pdf_tools': 8,
            'context7_text_tools': 5,
            'context7_developer_tools': 10
        };
        
        this.init();
    }

    async init() {
        try {
            await this.loadUserCredits();
            this.setupCreditDisplay();
            this.isInitialized = true;
            console.log('Universal Credit System initialized');
        } catch (error) {
            console.error('Failed to initialize credit system:', error);
            // Fallback to default free plan
            this.userCredits = {
                remaining: 50,
                total: 50,
                plan: 'free',
                type: 'daily'
            };
            this.isInitialized = true;
        }
    }

    async loadUserCredits() {
        try {
            // Try multiple endpoints to get user credit information
            let response = await fetch('/api/user-info');
            if (!response.ok) {
                response = await fetch('/payment/user-info');
            }

            if (response.ok) {
                const data = await response.json();
                console.log('Universal Credit System - Raw API response:', data);
                if (data.success && data.user_info) {
                    // Check if user is admin with unlimited credits
                    const isUnlimited = data.user_info.credits?.total === -1 ||
                                       data.user_info.credits?.remaining === -1 ||
                                       data.user_info.credits?.type === 'unlimited' ||
                                       data.user_info.plan_name === 'admin';
                    console.log('Universal Credit System - Admin check:', {
                        total: data.user_info.credits?.total,
                        remaining: data.user_info.credits?.remaining,
                        type: data.user_info.credits?.type,
                        plan: data.user_info.plan_name,
                        isUnlimited: isUnlimited
                    });

                    if (isUnlimited) {
                        this.userCredits = {
                            remaining: 'unlimited', // Use string for unlimited
                            total: 'unlimited',
                            plan: data.user_info.plan_name || 'admin',
                            type: 'unlimited',
                            isAdmin: true,
                            rawRemaining: -1, // Keep raw value for backend
                            rawTotal: -1
                        };
                        console.log('Universal Credit System - Admin user detected with unlimited credits');
                    } else {
                        this.userCredits = {
                            remaining: data.user_info.credits?.remaining || 50,
                            total: data.user_info.credits?.total || 50,
                            plan: data.user_info.plan_name || 'free',
                            type: data.user_info.credits?.type || 'daily',
                            isAdmin: false
                        };
                    }

                    console.log('Universal Credit System - Loaded credits:', this.userCredits);
                } else {
                    console.warn('Universal Credit System - No user info in response, using defaults');
                    this.setDefaultCredits();
                }
            } else {
                console.warn('Universal Credit System - Failed to fetch user info, using defaults');
                this.setDefaultCredits();
            }
        } catch (error) {
            console.error('Universal Credit System - Error loading user credits:', error);
            this.setDefaultCredits();
        }
    }

    setDefaultCredits() {
        this.userCredits = {
            remaining: 50,
            total: 50,
            plan: 'free',
            type: 'daily'
        };
    }

    setupCreditDisplay() {
        // Update sidebar credit display if it exists
        this.updateSidebarCredits();
        
        // Set up periodic credit refresh
        setInterval(() => {
            this.loadUserCredits().then(() => {
                this.updateSidebarCredits();
            });
        }, 30000); // Refresh every 30 seconds
    }

    updateSidebarCredits() {
        // Update sidebar dropdown credits (layout.html)
        this.updateDropdownCredits();

        // Update pricing page credits if on pricing page
        this.updatePricingPageCredits();

        // Update any other credit displays
        this.updateGenericCreditDisplays();
    }

    updateDropdownCredits() {
        // Update sidebar dropdown credits using existing functions
        if (typeof window.updateDropdownCredits === 'function') {
            window.updateDropdownCredits(
                this.userCredits.remaining,
                this.userCredits.total,
                this.userCredits.type
            );
        } else {
            // Fallback: Update elements directly
            const creditsDisplay = document.getElementById('dropdown-credits-count');
            const progressBar = document.getElementById('dropdown-credits-bar');
            const creditsText = document.getElementById('dropdown-credits-text');

            if (creditsDisplay) {
                if (this.userCredits.isAdmin && this.userCredits.type === 'unlimited') {
                    creditsDisplay.textContent = 'Unlimited';
                    creditsDisplay.style.fontSize = '14px';
                    creditsDisplay.className = 'text-lg font-bold text-purple-600';
                } else {
                    creditsDisplay.textContent = this.userCredits.remaining;
                    creditsDisplay.style.fontSize = '';
                    creditsDisplay.className = ''; // Reset class
                }
            }

            if (creditsText) {
                if (this.userCredits.isAdmin && this.userCredits.type === 'unlimited') {
                    creditsText.textContent = 'Admin - Unlimited Credits';
                } else if (this.userCredits.type === 'daily') {
                    creditsText.textContent = `${this.userCredits.remaining} remaining today`;
                } else {
                    creditsText.textContent = `${this.userCredits.remaining} remaining this month`;
                }
            }

            if (progressBar) {
                if (this.userCredits.isAdmin && this.userCredits.type === 'unlimited') {
                    // For admin users, show full progress bar with special styling
                    progressBar.style.width = '100%';
                    progressBar.className = 'h-1.5 rounded-full transition-all duration-300 bg-gradient-to-r from-purple-500 to-blue-500';
                    // creditsDisplay class is already set above
                } else {
                    const percentage = this.userCredits.total > 0 ?
                        (this.userCredits.remaining / this.userCredits.total) * 100 : 0;
                    progressBar.style.width = percentage + '%';

                    // Update colors based on credit level
                    if (this.userCredits.remaining <= 10) {
                        progressBar.className = 'h-1.5 rounded-full transition-all duration-300 bg-gradient-to-r from-red-600 to-red-800';
                        if (creditsDisplay) creditsDisplay.className = 'text-lg font-bold text-red-600';
                    } else if (this.userCredits.remaining <= 25) {
                        progressBar.className = 'h-1.5 rounded-full transition-all duration-300 bg-gradient-to-r from-yellow-500 to-orange-500';
                        if (creditsDisplay) creditsDisplay.className = 'text-lg font-bold text-yellow-600';
                    } else {
                        progressBar.className = 'h-1.5 rounded-full transition-all duration-300 bg-gradient-to-r from-green-500 to-emerald-500';
                        if (creditsDisplay) creditsDisplay.className = 'text-lg font-bold text-green-600';
                    }
                }
            }
        }
    }

    updatePricingPageCredits() {
        // Update pricing page credits using existing functions
        if (typeof window.updateCreditsDisplay === 'function') {
            window.updateCreditsDisplay(
                this.userCredits.remaining,
                this.userCredits.total,
                this.userCredits.type
            );
        } else {
            // Fallback: Update elements directly
            const creditsDisplay = document.getElementById('credits-display');
            const progressBar = document.getElementById('credits-progress-bar');
            const creditsText = document.getElementById('credits-text');
            const planDisplay = document.getElementById('current-plan-display');

            if (creditsDisplay) {
                if (this.userCredits.isAdmin && this.userCredits.type === 'unlimited') {
                    creditsDisplay.textContent = 'Unlimited';
                    creditsDisplay.style.color = '#7c3aed'; // Purple color
                    creditsDisplay.style.fontWeight = 'bold';
                } else {
                    creditsDisplay.textContent = this.userCredits.remaining;
                    creditsDisplay.style.color = ''; // Reset color
                    creditsDisplay.style.fontWeight = '';
                }
            }

            if (planDisplay) {
                if (this.userCredits.isAdmin && this.userCredits.type === 'unlimited') {
                    planDisplay.textContent = 'Admin Plan';
                } else {
                    planDisplay.textContent = this.userCredits.plan.charAt(0).toUpperCase() + this.userCredits.plan.slice(1) + ' Plan';
                }
            }

            if (creditsText) {
                if (this.userCredits.isAdmin && this.userCredits.type === 'unlimited') {
                    creditsText.textContent = 'Unlimited credits - Admin access';
                } else if (this.userCredits.type === 'daily') {
                    creditsText.textContent = `${this.userCredits.remaining} credits remaining today (resets daily)`;
                } else if (this.userCredits.type === 'monthly') {
                    creditsText.textContent = `${this.userCredits.remaining} credits remaining this month`;
                } else {
                    creditsText.textContent = `${this.userCredits.remaining} credits remaining`;
                }
            }

            if (progressBar) {
                if (this.userCredits.isAdmin && this.userCredits.type === 'unlimited') {
                    // For admin users, show full progress bar with special styling
                    progressBar.style.width = '100%';
                    progressBar.className = 'h-3 rounded-full transition-all duration-300 bg-gradient-to-r from-purple-600 to-blue-600';
                    // Don't override creditsDisplay color here - it's set above
                } else {
                    const percentage = this.userCredits.total > 0 ?
                        (this.userCredits.remaining / this.userCredits.total) * 100 : 0;
                    progressBar.style.width = percentage + '%';

                    // Update colors based on credit level
                    if (this.userCredits.remaining <= 10) {
                        progressBar.className = 'h-3 rounded-full transition-all duration-300 bg-gradient-to-r from-red-600 to-red-800';
                        if (creditsDisplay) creditsDisplay.style.color = '#dc2626';
                    } else if (this.userCredits.remaining <= 25) {
                        progressBar.className = 'h-3 rounded-full transition-all duration-300 bg-gradient-to-r from-yellow-500 to-orange-500';
                        if (creditsDisplay) creditsDisplay.style.color = '#d97706';
                    } else {
                        progressBar.className = 'h-3 rounded-full transition-all duration-300 bg-gradient-to-r from-green-500 to-emerald-500';
                        if (creditsDisplay) creditsDisplay.style.color = '#059669';
                    }
                }
            }
        }
    }

    updateGenericCreditDisplays() {
        // Update any generic credit displays
        const creditElements = document.querySelectorAll('.credit-display, #userCredits, .credits-remaining');
        creditElements.forEach(element => {
            if (element && !element.id.includes('dropdown') && !element.id.includes('credits-display')) {
                const percentage = this.userCredits.total > 0 ?
                    (this.userCredits.remaining / this.userCredits.total) * 100 : 0;

                element.innerHTML = `
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-300">Credits</span>
                        <span class="text-sm font-medium ${this.userCredits.remaining < 10 ? 'text-red-400' : 'text-green-400'}">
                            ${this.userCredits.remaining}/${this.userCredits.total}
                        </span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2 mt-1">
                        <div class="bg-gradient-to-r ${percentage > 20 ? 'from-green-500 to-blue-500' : 'from-red-500 to-orange-500'} h-2 rounded-full transition-all duration-300"
                             style="width: ${percentage}%"></div>
                    </div>
                    <div class="text-xs text-gray-400 mt-1">
                        ${this.userCredits.plan.charAt(0).toUpperCase() + this.userCredits.plan.slice(1)} Plan
                        ${this.userCredits.type === 'daily' ? '(resets daily)' : ''}
                    </div>
                `;
            }
        });
    }

    getTaskCreditCost(taskType) {
        return this.creditCosts[taskType] || 1;
    }

    async checkCredits(taskType, customAmount = null) {
        if (!this.isInitialized) {
            await this.init();
        }

        const creditCost = customAmount || this.getTaskCreditCost(taskType);

        // Unlimited plans always have access
        if (this.userCredits.plan === 'pro' || this.userCredits.type === 'unlimited') {
            return {
                hasCredits: true,
                remaining: -1,
                cost: creditCost,
                plan: this.userCredits.plan
            };
        }

        // Check if user has enough credits
        const hasCredits = this.userCredits.remaining >= creditCost;

        return {
            hasCredits,
            remaining: this.userCredits.remaining,
            cost: creditCost,
            plan: this.userCredits.plan,
            needed: creditCost - this.userCredits.remaining
        };
    }

    async consumeCredits(taskType, customAmount = null) {
        const creditCheck = await this.checkCredits(taskType, customAmount);

        if (!creditCheck.hasCredits) {
            return {
                success: false,
                error: 'Insufficient credits',
                ...creditCheck
            };
        }

        try {
            const response = await fetch('/api/consume-credits', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    task_type: taskType,
                    amount: customAmount
                })
            });

            const result = await response.json();

            if (result.success) {
                // Update local credit state
                if (this.userCredits.isAdmin && this.userCredits.type === 'unlimited') {
                    // For admin users, keep unlimited status
                    this.userCredits.remaining = 'unlimited';
                    console.log(`Admin user: Credit consumed but unlimited access maintained`);
                } else {
                    // For regular users, use actual remaining credits from server
                    this.userCredits.remaining = result.remaining_credits;
                }

                // Update all credit displays immediately
                this.updateSidebarCredits();

                // Also trigger global refresh if available
                if (window.refreshCredits) {
                    window.refreshCredits();
                }

                return {
                    success: true,
                    consumed: result.credits_consumed,
                    remaining: this.userCredits.remaining
                };
            } else {
                return {
                    success: false,
                    error: result.error || 'Failed to consume credits'
                };
            }
        } catch (error) {
            console.error('Error consuming credits:', error);
            return {
                success: false,
                error: 'Network error'
            };
        }
    }

    showInsufficientCreditsModal(taskType, creditCheck) {
        const modal = this.createInsufficientCreditsModal(taskType, creditCheck);
        document.body.appendChild(modal);

        // Show modal with animation
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }

    createInsufficientCreditsModal(taskType, creditCheck) {
        const modal = document.createElement('div');
        modal.className = 'credit-modal-overlay';
        modal.innerHTML = `
            <div class="credit-modal">
                <div class="credit-modal-header">
                    <h3>💳 Insufficient Credits</h3>
                    <button class="credit-modal-close" onclick="this.closest('.credit-modal-overlay').remove()">×</button>
                </div>
                <div class="credit-modal-body">
                    <div class="credit-info">
                        <p><strong>${this.getTaskDisplayName(taskType)}</strong> requires <strong>${creditCheck.cost} credits</strong></p>
                        <div class="credit-status">
                            <span>Available Credits: <strong class="text-red-400">${creditCheck.remaining}</strong></span>
                            <span>Credits Needed: <strong class="text-orange-400">${creditCheck.needed > 0 ? creditCheck.needed : 0}</strong></span>
                        </div>
                        <p class="current-plan">Current Plan: <strong>${creditCheck.plan.charAt(0).toUpperCase() + creditCheck.plan.slice(1)}</strong></p>
                        ${creditCheck.plan === 'free' ? '<p class="reset-info">💡 Free plan credits reset daily (50 credits)</p>' : ''}
                    </div>
                    <div class="upgrade-options">
                        <h4>💳 Upgrade Your Plan</h4>
                        <p>To access all AutoWave features with sufficient credits, please upgrade your plan.</p>
                        <div class="upgrade-buttons">
                            <button class="upgrade-btn upgrade-btn-plus" onclick="window.location.href='/pricing'">
                                Plus Plan - $15/month<br>
                                <small>8,000 credits/month</small>
                            </button>
                            <button class="upgrade-btn upgrade-btn-pro" onclick="window.location.href='/pricing'">
                                Pro Plan - $169/month<br>
                                <small>Unlimited credits</small>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal styles
        this.addModalStyles();

        return modal;
    }

    getTaskDisplayName(taskType) {
        const displayNames = {
            'chat_message': 'Chat Message',
            'autowave_chat_basic': 'AutoWave Chat',
            'autowave_chat_advanced': 'Advanced Chat',
            'prime_agent_task': 'Prime Agent Task',
            'prime_agent_complex': 'Complex Prime Agent Task',
            'agent_wave_document': 'Document Generation',
            'research_basic': 'Basic Research',
            'research_advanced': 'Advanced Research',
            'research_comprehensive': 'Comprehensive Research',
            'code_generation_simple': 'Simple Code Generation',
            'code_generation_advanced': 'Advanced Code Generation',
            'code_generation_complex': 'Complex Code Generation',
            'context7_package_tracking': 'Package Tracking',
            'context7_restaurant_booking': 'Restaurant Booking',
            'context7_real_estate': 'Real Estate Search',
            'context7_flight_search': 'Flight Search',
            'context7_hotel_booking': 'Hotel Booking',
            'context7_travel_planning': 'Travel Planning',
            'context7_job_search': 'Job Search'
        };

        return displayNames[taskType] || taskType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    addModalStyles() {
        if (document.getElementById('credit-modal-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'credit-modal-styles';
        styles.textContent = `
            .credit-modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                opacity: 0;
                transition: opacity 0.3s ease;
            }

            .credit-modal-overlay.show {
                opacity: 1;
            }

            .credit-modal {
                background: #1f2937;
                border-radius: 12px;
                max-width: 500px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                border: 1px solid #374151;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
                transform: scale(0.9);
                transition: transform 0.3s ease;
            }

            .credit-modal-overlay.show .credit-modal {
                transform: scale(1);
            }

            .credit-modal-header {
                display: flex;
                justify-content: between;
                align-items: center;
                padding: 20px;
                border-bottom: 1px solid #374151;
                background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
                border-radius: 12px 12px 0 0;
            }

            .credit-modal-header h3 {
                margin: 0;
                color: #f9fafb;
                font-size: 1.25rem;
                font-weight: 600;
                flex: 1;
            }

            .credit-modal-close {
                background: none;
                border: none;
                color: #9ca3af;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                transition: all 0.2s ease;
            }

            .credit-modal-close:hover {
                background: #374151;
                color: #f9fafb;
            }

            .credit-modal-body {
                padding: 20px;
                color: #e5e7eb;
            }

            .credit-info {
                margin-bottom: 24px;
                padding: 16px;
                background: #111827;
                border-radius: 8px;
                border-left: 4px solid #ef4444;
            }

            .credit-status {
                display: flex;
                justify-content: space-between;
                margin: 12px 0;
                font-size: 0.9rem;
            }

            .current-plan {
                margin: 8px 0;
                font-size: 0.9rem;
                color: #9ca3af;
            }

            .reset-info {
                margin: 8px 0;
                font-size: 0.85rem;
                color: #60a5fa;
                font-style: italic;
            }

            .upgrade-options h4 {
                margin: 0 0 12px 0;
                color: #f9fafb;
                font-size: 1.1rem;
            }

            .upgrade-buttons {
                display: flex;
                gap: 12px;
                margin-top: 16px;
            }

            .upgrade-btn {
                flex: 1;
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 500;
                text-align: center;
                transition: all 0.2s ease;
                font-size: 0.9rem;
                line-height: 1.4;
            }

            .upgrade-btn-plus {
                background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                color: white;
            }

            .upgrade-btn-plus:hover {
                background: linear-gradient(135deg, #2563eb, #7c3aed);
                transform: translateY(-1px);
            }

            .upgrade-btn-pro {
                background: linear-gradient(135deg, #059669, #0d9488);
                color: white;
            }

            .upgrade-btn-pro:hover {
                background: linear-gradient(135deg, #047857, #0f766e);
                transform: translateY(-1px);
            }

            .text-red-400 { color: #f87171; }
            .text-orange-400 { color: #fb923c; }
        `;

        document.head.appendChild(styles);
    }

    // Helper method to check and enforce credits before any action
    async enforceCredits(taskType, customAmount = null) {
        const creditCheck = await this.checkCredits(taskType, customAmount);

        if (!creditCheck.hasCredits) {
            this.showInsufficientCreditsModal(taskType, creditCheck);
            return false;
        }

        return true;
    }

    // Helper method to check, enforce, and consume credits in one call
    async checkAndConsumeCredits(taskType, customAmount = null) {
        const canProceed = await this.enforceCredits(taskType, customAmount);

        if (!canProceed) {
            return { success: false, error: 'Insufficient credits' };
        }

        return await this.consumeCredits(taskType, customAmount);
    }

    // Method to handle plan upgrades and credit updates
    updatePlan(planName, credits) {
        console.log('Universal Credit System - Updating plan:', planName, credits);

        this.userCredits.plan = planName.toLowerCase();

        // Set credit totals based on plan
        switch(planName.toLowerCase()) {
            case 'free':
                this.userCredits.total = 50;
                this.userCredits.type = 'daily';
                this.userCredits.remaining = credits?.remaining || 50;
                break;
            case 'plus':
                this.userCredits.total = 8000;
                this.userCredits.type = 'monthly';
                this.userCredits.remaining = credits?.remaining || 8000;
                break;
            case 'pro':
                this.userCredits.total = 200000;
                this.userCredits.type = 'unlimited';
                this.userCredits.remaining = credits?.remaining || 200000;
                break;
            default:
                this.userCredits.total = 50;
                this.userCredits.type = 'daily';
                this.userCredits.remaining = credits?.remaining || 50;
        }

        // Update all displays
        this.updateSidebarCredits();

        console.log('Universal Credit System - Plan updated to:', this.userCredits);
    }

    // Method to refresh credits from server
    async refreshFromServer() {
        console.log('Universal Credit System - Refreshing from server...');
        await this.loadUserCredits();
        this.updateSidebarCredits();
    }

    // Method to get current credit status
    getCreditStatus() {
        return {
            remaining: this.userCredits.remaining,
            total: this.userCredits.total,
            plan: this.userCredits.plan,
            type: this.userCredits.type,
            percentage: this.userCredits.total > 0 ?
                (this.userCredits.remaining / this.userCredits.total) * 100 : 0
        };
    }
}

// Create global instance
window.creditSystem = new UniversalCreditSystem();

// Make refresh function globally available
window.refreshUniversalCredits = function() {
    if (window.creditSystem) {
        window.creditSystem.refreshFromServer();
    }
};

// Override existing global functions to work with Universal Credit System
window.addEventListener('load', function() {
    // Override existing consumeCredits function if it exists
    if (window.consumeCredits) {
        const originalConsumeCredits = window.consumeCredits;
        window.consumeCredits = async function(taskType, amount = null) {
            // Use Universal Credit System first
            if (window.creditSystem) {
                const result = await window.creditSystem.consumeCredits(taskType, amount);
                if (result.success) {
                    return result;
                }
            }
            // Fallback to original function
            return originalConsumeCredits(taskType, amount);
        };
    }
});
