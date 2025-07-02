/**
 * AutoWave Referral System Frontend
 * Handles UTM tracking, referral codes, and discount display
 */

class ReferralManager {
    constructor() {
        this.referralData = null;
        this.init();
    }

    async init() {
        // Check for UTM parameters in URL
        this.checkUTMParameters();
        
        // Load current referral status
        await this.loadReferralStatus();
        
        // Initialize UI components
        this.initializeUI();
    }

    checkUTMParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        const utmParams = {};
        
        // Check for UTM parameters
        ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(param => {
            if (urlParams.has(param)) {
                utmParams[param] = urlParams.get(param);
            }
        });

        // Check for referral code parameter
        const refCode = urlParams.get('ref') || urlParams.get('referral_code');
        
        // If we have UTM parameters or referral code, track them
        if (Object.keys(utmParams).length > 0 || refCode) {
            this.trackReferral(utmParams, refCode);
        }
    }

    async trackReferral(utmParams, referralCode) {
        try {
            const params = new URLSearchParams();
            
            // Add UTM parameters
            Object.keys(utmParams).forEach(key => {
                params.append(key, utmParams[key]);
            });
            
            // Add referral code if present
            if (referralCode) {
                params.append('referral_code', referralCode);
            }

            const response = await fetch(`/referral/track?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            
            if (result.success && result.referral_active) {
                this.referralData = result;
                this.showReferralWelcome(result);
                this.updatePricingDisplay();
            }
        } catch (error) {
            console.error('Error tracking referral:', error);
        }
    }

    async loadReferralStatus() {
        try {
            const response = await fetch('/referral/status');
            const result = await response.json();
            
            if (result.success && result.has_referral) {
                this.referralData = result;
                this.updatePricingDisplay();
            }
        } catch (error) {
            console.error('Error loading referral status:', error);
        }
    }

    async applyReferralCode(code) {
        try {
            const response = await fetch('/referral/apply-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ referral_code: code })
            });

            const result = await response.json();
            
            if (result.success) {
                this.referralData = result;
                this.showSuccessMessage(result.message);
                this.updatePricingDisplay();
                return true;
            } else {
                this.showErrorMessage(result.error);
                return false;
            }
        } catch (error) {
            console.error('Error applying referral code:', error);
            this.showErrorMessage('Failed to apply referral code');
            return false;
        }
    }

    initializeUI() {
        // Add referral code input to pricing page if it exists
        this.addReferralCodeInput();
        
        // Add referral status display
        this.addReferralStatusDisplay();
        
        // Update pricing displays
        this.updatePricingDisplay();
    }

    addReferralCodeInput() {
        // Look for pricing forms or subscription buttons
        const pricingContainer = document.querySelector('.pricing-container, .subscription-form, .payment-form');
        
        if (pricingContainer && !document.getElementById('referral-code-input')) {
            const referralHTML = `
                <div id="referral-code-section" class="referral-code-section" style="margin: 20px 0; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #f9f9f9;">
                    <h4 style="margin: 0 0 10px 0; color: #333;">Have a Referral Code?</h4>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <input 
                            type="text" 
                            id="referral-code-input" 
                            placeholder="Enter referral code (e.g., MATTHEW20)" 
                            style="flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                        />
                        <button 
                            id="apply-referral-btn" 
                            style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;"
                        >
                            Apply
                        </button>
                    </div>
                    <div id="referral-message" style="margin-top: 10px; font-size: 13px;"></div>
                </div>
            `;
            
            pricingContainer.insertAdjacentHTML('afterbegin', referralHTML);
            
            // Add event listeners
            document.getElementById('apply-referral-btn').addEventListener('click', () => {
                const code = document.getElementById('referral-code-input').value.trim();
                if (code) {
                    this.applyReferralCode(code);
                }
            });
            
            document.getElementById('referral-code-input').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const code = e.target.value.trim();
                    if (code) {
                        this.applyReferralCode(code);
                    }
                }
            });
        }
    }

    addReferralStatusDisplay() {
        // Add a floating referral status indicator
        if (this.referralData && this.referralData.discount_percentage > 0 && !document.getElementById('referral-status-indicator')) {
            const statusHTML = `
                <div id="referral-status-indicator" style="
                    position: fixed; 
                    top: 20px; 
                    right: 20px; 
                    background: linear-gradient(135deg, #28a745, #20c997); 
                    color: white; 
                    padding: 12px 16px; 
                    border-radius: 8px; 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
                    z-index: 1000;
                    font-size: 14px;
                    font-weight: 500;
                    max-width: 250px;
                ">
                    🎉 <strong>${this.referralData.discount_percentage}% OFF</strong><br>
                    <small>+ ${this.referralData.bonus_credits} bonus credits</small>
                    <button onclick="this.parentElement.style.display='none'" style="
                        position: absolute; 
                        top: 5px; 
                        right: 8px; 
                        background: none; 
                        border: none; 
                        color: white; 
                        cursor: pointer; 
                        font-size: 16px;
                    ">×</button>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', statusHTML);
        }
    }

    updatePricingDisplay() {
        if (!this.referralData || this.referralData.discount_percentage === 0) return;

        // Find all price elements and update them
        const priceElements = document.querySelectorAll('.price, .pricing-amount, [data-price]');
        
        priceElements.forEach(element => {
            const originalPrice = parseFloat(element.textContent.replace(/[^0-9.]/g, ''));
            if (originalPrice && originalPrice > 0) {
                const discountedPrice = originalPrice * (1 - this.referralData.discount_percentage / 100);
                const savings = originalPrice - discountedPrice;
                
                // Add discount display
                if (!element.querySelector('.referral-discount')) {
                    const discountHTML = `
                        <div class="referral-discount" style="margin-top: 5px;">
                            <span style="text-decoration: line-through; color: #999; font-size: 0.9em;">$${originalPrice.toFixed(2)}</span>
                            <span style="color: #28a745; font-weight: bold; margin-left: 8px;">$${discountedPrice.toFixed(2)}</span>
                            <div style="color: #28a745; font-size: 0.8em;">Save $${savings.toFixed(2)} with referral!</div>
                        </div>
                    `;
                    element.insertAdjacentHTML('afterend', discountHTML);
                }
            }
        });
    }

    showReferralWelcome(data) {
        // Show a welcome message for new referrals
        const welcomeHTML = `
            <div id="referral-welcome" style="
                position: fixed; 
                top: 50%; 
                left: 50%; 
                transform: translate(-50%, -50%); 
                background: white; 
                padding: 30px; 
                border-radius: 12px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.2); 
                z-index: 10000;
                text-align: center;
                max-width: 400px;
            ">
                <h3 style="color: #28a745; margin: 0 0 15px 0;">🎉 Welcome!</h3>
                <p style="margin: 0 0 20px 0; color: #333;">
                    ${data.message}
                </p>
                <button onclick="document.getElementById('referral-welcome').remove()" style="
                    background: #28a745; 
                    color: white; 
                    border: none; 
                    padding: 10px 20px; 
                    border-radius: 6px; 
                    cursor: pointer;
                    font-size: 14px;
                ">
                    Awesome!
                </button>
            </div>
            <div style="
                position: fixed; 
                top: 0; 
                left: 0; 
                width: 100%; 
                height: 100%; 
                background: rgba(0,0,0,0.5); 
                z-index: 9999;
            " onclick="document.getElementById('referral-welcome').remove(); this.remove();"></div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', welcomeHTML);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const welcome = document.getElementById('referral-welcome');
            if (welcome) {
                welcome.remove();
                document.querySelector('[style*="rgba(0,0,0,0.5)"]')?.remove();
            }
        }, 5000);
    }

    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }

    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        const messageEl = document.getElementById('referral-message');
        if (messageEl) {
            messageEl.innerHTML = message;
            messageEl.style.color = type === 'success' ? '#28a745' : '#dc3545';
            messageEl.style.fontWeight = 'bold';
            
            // Clear message after 5 seconds
            setTimeout(() => {
                messageEl.innerHTML = '';
            }, 5000);
        }
    }

    // Method to get current referral data for checkout
    getReferralData() {
        return this.referralData;
    }

    // Method to generate referral links (for influencers)
    async generateReferralLink(influencerId, baseUrl = window.location.origin) {
        try {
            const response = await fetch(`/referral/generate-link/${influencerId}?base_url=${encodeURIComponent(baseUrl)}`);
            const result = await response.json();
            
            if (result.success) {
                return result.referral_link;
            }
        } catch (error) {
            console.error('Error generating referral link:', error);
        }
        return null;
    }
}

// Initialize referral manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.referralManager = new ReferralManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ReferralManager;
}
